"""
T6.5: End-to-end render orchestrator.

Coordinates all T6 components (production rendering, concatenation, thumbnails, caching)
into a complete video rendering pipeline with comprehensive logging and metrics.
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from . import RenderInput, RenderResult, SceneRenderItem
from .manim_prod import ProductionManimRenderer, ProductionRenderResult
from .concat import VideoConcatenator, ConcatResult
from .thumbs import ThumbnailGenerator, generate_standard_thumbnails
from .cache import RenderCache, CachedOperation
from .config import validate_render_input, get_quality_preset
from .errors import (
    RenderSceneError,
    RenderTimeoutError,
    RenderOOMError,
    ConcatError,
    ThumbnailError,
    ValidationError,
)
from .metrics import (
    render_metrics_context,
    get_metrics_collector,
    get_structured_logger,
    ConcatMetrics,
    ThumbnailMetrics,
)


class RenderOrchestrator:
    """T6.5: Complete video rendering orchestrator."""

    def __init__(
        self,
        cache: RenderCache = None,
        enable_caching: bool = True,
        temp_dir: Path = None,
        logger: logging.Logger = None,
    ):
        """
        Initialize render orchestrator.

        Args:
            cache: Render cache instance
            enable_caching: Whether to use caching
            temp_dir: Temporary directory for operations
            logger: Logger instance
        """
        self.cache = cache or RenderCache() if enable_caching else None
        self.enable_caching = enable_caching and self.cache is not None
        self.temp_dir = temp_dir
        self.logger = logger or self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Setup default logger for render operations."""
        logger = logging.getLogger("render_orchestrator")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def render_video(self, rin: RenderInput) -> RenderResult:
        """
        Execute complete video rendering pipeline.

        Args:
            rin: Complete render input specification

        Returns:
            RenderResult with final video and artifacts
        """
        structured_logger = get_structured_logger()

        # Use metrics context for the entire render operation
        with render_metrics_context("video_render", rin.video_id) as render_metrics:
            logs = {
                "video_id": rin.video_id,
                "quality": rin.quality,
                "scenes": [s.scene_id for s in rin.scenes],
                "crossfade_s": rin.crossfade_s,
            }

            try:
                # Validate input
                try:
                    validate_render_input(rin)
                except (ValueError, TypeError) as e:
                    raise ValidationError(
                        field="render_input", value=str(rin), constraint=str(e)
                    )

                self.logger.info(
                    f"Starting video render: {rin.video_id} ({len(rin.scenes)} scenes)"
                )
                structured_logger.log_structured(
                    "info",
                    "video_render_start",
                    video_id=rin.video_id,
                    scene_count=len(rin.scenes),
                    quality=rin.quality,
                    crossfade_s=rin.crossfade_s,
                )

                # Step 1: Render individual scenes
                scene_results = self._render_all_scenes(rin, logs)

                # Check if all scenes rendered successfully
                failed_scenes = [r for r in scene_results if not r.success]
                if failed_scenes:
                    error_msg = f"{len(failed_scenes)} scenes failed to render"
                    self.logger.error(error_msg)
                    structured_logger.log_error(
                        "scene_render_failures",
                        error_msg,
                        failed_count=len(failed_scenes),
                        video_id=rin.video_id,
                    )
                    return self._create_error_result(
                        error_msg, logs, render_metrics.start_time
                    )

                scene_mp4s = [r.output_mp4 for r in scene_results if r.output_mp4]
                logs["scene_render_results"] = [
                    self._summarize_scene_result(r) for r in scene_results
                ]

                # Step 2: Concatenate scenes
                concat_result = self._concatenate_scenes(rin, scene_mp4s, logs)
                if not concat_result.success:
                    error_msg = (
                        f"Scene concatenation failed: {concat_result.error_message}"
                    )
                    self.logger.error(error_msg)
                    return self._create_error_result(
                        error_msg, logs, render_metrics.start_time
                    )

                logs["concat_result"] = self._summarize_concat_result(concat_result)

                # Step 3: Generate thumbnails
                thumbnails = self._generate_thumbnails(
                    concat_result.output_video, rin, logs
                )
                logs["thumbnails_generated"] = len(thumbnails)

                # Update render metrics
                render_metrics.file_size_mb = concat_result.file_size_mb
                render_metrics.additional_data = {
                    "scenes_rendered": len(scene_results),
                    "thumbnails_generated": len(thumbnails),
                    "concat_duration_s": concat_result.duration_s,
                    "total_scenes": len(rin.scenes),
                }

                # Success!
                total_time = time.time() - render_metrics.start_time
                logs["total_duration_s"] = total_time
                logs["success"] = True

                self.logger.info(
                    f"Video render completed: {rin.video_id} "
                    f"({total_time:.1f}s, {concat_result.file_size_mb:.1f}MB)"
                )

                return RenderResult(
                    ok=True,
                    final_mp4=concat_result.output_video,
                    scene_mp4s=scene_mp4s,
                    thumbs=thumbnails,
                    logs=logs,
                )

            except Exception as e:
                error_msg = f"Render orchestration failed: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                return self._create_error_result(
                    error_msg, logs, render_metrics.start_time
                )

    def _render_all_scenes(
        self, rin: RenderInput, logs: Dict[str, Any]
    ) -> List[ProductionRenderResult]:
        """Render all scenes in the video."""
        scene_results = []
        scenes_output_dir = rin.out_dir / "scenes"
        scenes_output_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Rendering {len(rin.scenes)} scenes in {rin.quality} quality")

        # Check for cached renders first
        cached_scenes = []
        scenes_to_render = []

        for scene in rin.scenes:
            if self.enable_caching:
                cached_result = self._check_scene_cache(scene, rin, scenes_output_dir)
                if cached_result:
                    scene_results.append(cached_result)
                    cached_scenes.append(scene.scene_id)
                    continue

            scenes_to_render.append(scene)

        if cached_scenes:
            self.logger.info(
                f"Using cached renders for {len(cached_scenes)} scenes: {cached_scenes}"
            )

        # Render remaining scenes
        if scenes_to_render:
            with ProductionManimRenderer(
                quality=rin.quality, work_dir=self.temp_dir
            ) as renderer:
                for scene in scenes_to_render:
                    self.logger.info(f"Rendering scene: {scene.scene_id}")

                    result = renderer.render_scene(scene, scenes_output_dir)
                    scene_results.append(result)

                    if result.success:
                        self.logger.info(
                            f"Scene {scene.scene_id} rendered: "
                            f"{result.render_time_s:.1f}s, {result.file_size_mb:.1f}MB"
                        )

                        # Cache successful render
                        if self.enable_caching:
                            self._cache_scene_result(scene, rin, result)
                    else:
                        self.logger.error(
                            f"Scene {scene.scene_id} failed: {result.error_message}"
                        )

        # Ensure results are in same order as input scenes
        scene_id_to_result = {
            self._extract_scene_id_from_result(r): r for r in scene_results
        }
        ordered_results = []
        for scene in rin.scenes:
            result = scene_id_to_result.get(scene.scene_id)
            if result:
                ordered_results.append(result)

        return ordered_results

    def _check_scene_cache(
        self, scene: SceneRenderItem, rin: RenderInput, output_dir: Path
    ) -> Optional[ProductionRenderResult]:
        """Check if scene render is cached."""
        if not self.cache:
            return None

        try:
            # Create cache key
            scene_content = scene.main_py.read_text()
            cache_key = self.cache.create_scene_render_key(
                scene_content=scene_content,
                quality=rin.quality,
                timeout_s=180,  # Standard timeout
                additional_params={"fps": rin.fps},
            )

            with CachedOperation(self.cache, cache_key, "scene_render") as op:
                if op.is_cached():
                    cached_files = op.get_cached_files()
                    metadata = op.get_cached_metadata()

                    if cached_files:
                        # Copy cached file to output directory
                        cached_mp4 = cached_files[0]  # First file should be the MP4
                        output_mp4 = output_dir / f"scene_{scene.scene_id}_prod.mp4"

                        import shutil

                        shutil.copy2(cached_mp4, output_mp4)

                        # Create result from cached metadata
                        return ProductionRenderResult(
                            success=True,
                            output_mp4=output_mp4,
                            duration_s=metadata.get("duration_s", 0.0),
                            file_size_mb=output_mp4.stat().st_size / (1024 * 1024),
                            resolution=tuple(metadata.get("resolution", (0, 0))),
                            fps=metadata.get("fps", rin.fps),
                            frame_count=metadata.get("frame_count", 0),
                            render_time_s=0.0,  # Cached, so no render time
                            stdout="[cached]",
                            stderr="",
                        )

        except Exception as e:
            self.logger.warning(f"Cache check failed for scene {scene.scene_id}: {e}")

        return None

    def _cache_scene_result(
        self, scene: SceneRenderItem, rin: RenderInput, result: ProductionRenderResult
    ):
        """Cache successful scene render result."""
        if not self.cache or not result.success or not result.output_mp4:
            return

        try:
            scene_content = scene.main_py.read_text()
            cache_key = self.cache.create_scene_render_key(
                scene_content=scene_content,
                quality=rin.quality,
                timeout_s=180,
                additional_params={"fps": rin.fps},
            )

            metadata = {
                "scene_id": scene.scene_id,
                "class_name": scene.class_name,
                "quality": rin.quality,
                "duration_s": result.duration_s,
                "resolution": result.resolution,
                "fps": result.fps,
                "frame_count": result.frame_count,
                "render_time_s": result.render_time_s,
            }

            with CachedOperation(self.cache, cache_key, "scene_render") as op:
                op.cache_result([result.output_mp4], metadata)

        except Exception as e:
            self.logger.warning(f"Failed to cache scene {scene.scene_id}: {e}")

    def _concatenate_scenes(
        self, rin: RenderInput, scene_mp4s: List[Path], logs: Dict[str, Any]
    ) -> ConcatResult:
        """Concatenate scene videos into final video."""
        final_mp4_path = rin.out_dir / f"{rin.video_id}_final.mp4"
        quality_preset = get_quality_preset(rin.quality)
        metrics_collector = get_metrics_collector()

        self.logger.info(f"Concatenating {len(scene_mp4s)} scenes")

        start_time = time.time()
        with VideoConcatenator(
            quality_preset=quality_preset, temp_dir=self.temp_dir
        ) as concatenator:
            result = concatenator.concatenate_videos(
                input_videos=scene_mp4s,
                output_video=final_mp4_path,
                crossfade_s=rin.crossfade_s,
            )

        # Record concat metrics
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        concat_metrics = ConcatMetrics(
            video_id=rin.video_id,
            input_count=len(scene_mp4s),
            output_duration_s=result.duration_s if result.success else 0.0,
            crossfade_used=rin.crossfade_s is not None,
            crossfade_duration_s=rin.crossfade_s,
            transitions_applied=result.transitions_applied if result.success else 0,
            re_encodes=1 if rin.crossfade_s else 0,  # Simplified count
            total_latency_ms=processing_time,
            success=result.success,
            error_type=type(result).__name__ if not result.success else None,
        )
        metrics_collector.record_concat_metrics(concat_metrics)

        return result

    def _generate_thumbnails(
        self, final_video: Path, rin: RenderInput, logs: Dict[str, Any]
    ) -> List[Path]:
        """Generate thumbnails for the final video."""
        if not final_video or not final_video.exists():
            return []

        thumbs_dir = rin.out_dir / "thumbnails"
        thumbs_dir.mkdir(parents=True, exist_ok=True)
        metrics_collector = get_metrics_collector()

        self.logger.info("Generating thumbnails")

        try:
            start_time = time.time()
            thumbnail_results = generate_standard_thumbnails(
                video_path=final_video, output_dir=thumbs_dir, video_name=rin.video_id
            )
            processing_time = (time.time() - start_time) * 1000  # Convert to ms

            successful_thumbs = [
                result.thumbnail_path
                for result in thumbnail_results
                if result.success and result.thumbnail_path
            ]

            # Record thumbnail metrics for each type
            for result in thumbnail_results:
                thumbnail_type = (
                    "poster" if "poster" in str(result.thumbnail_path) else "standard"
                )
                if "mid" in str(result.thumbnail_path):
                    thumbnail_type = "midpoint"

                thumbnail_metrics = ThumbnailMetrics(
                    video_id=rin.video_id,
                    thumbnail_type=thumbnail_type,
                    extraction_time_ms=(
                        result.extraction_time_s * 1000
                        if hasattr(result, "extraction_time_s")
                        else processing_time
                    ),
                    source_duration_s=(
                        result.source_time_s
                        if hasattr(result, "source_time_s")
                        else 0.0
                    ),
                    success=result.success,
                    error_type=None if result.success else "ThumbnailError",
                )
                metrics_collector.record_thumbnail_metrics(thumbnail_metrics)

            self.logger.info(f"Generated {len(successful_thumbs)} thumbnails")
            return successful_thumbs

        except Exception as e:
            self.logger.warning(f"Thumbnail generation failed: {e}")

            # Record failure metrics
            thumbnail_metrics = ThumbnailMetrics(
                video_id=rin.video_id,
                thumbnail_type="failed",
                extraction_time_ms=0.0,
                source_duration_s=0.0,
                success=False,
                error_type=type(e).__name__,
            )
            metrics_collector.record_thumbnail_metrics(thumbnail_metrics)

            return []

    def _extract_scene_id_from_result(self, result: ProductionRenderResult) -> str:
        """Extract scene ID from render result filename."""
        if result.output_mp4:
            # Extract from filename like "scene_sec_01_prod.mp4"
            stem = result.output_mp4.stem
            if stem.startswith("scene_") and stem.endswith("_prod"):
                return stem[6:-5]  # Remove "scene_" and "_prod"
        return "unknown"

    def _summarize_scene_result(self, result: ProductionRenderResult) -> Dict[str, Any]:
        """Create summary of scene render result for logs."""
        return {
            "success": result.success,
            "duration_s": result.duration_s,
            "file_size_mb": result.file_size_mb,
            "render_time_s": result.render_time_s,
            "resolution": result.resolution,
            "fps": result.fps,
            "error": result.error_message if not result.success else None,
        }

    def _summarize_concat_result(self, result: ConcatResult) -> Dict[str, Any]:
        """Create summary of concatenation result for logs."""
        return {
            "success": result.success,
            "duration_s": result.duration_s,
            "file_size_mb": result.file_size_mb,
            "processing_time_s": result.processing_time_s,
            "transitions_applied": result.transitions_applied,
            "error": result.error_message if not result.success else None,
        }

    def _create_error_result(
        self, error_message: str, logs: Dict[str, Any], start_time: float
    ) -> RenderResult:
        """Create error result with logs."""
        logs.update(
            {
                "success": False,
                "error_message": error_message,
                "total_duration_s": time.time() - start_time,
            }
        )

        return RenderResult(
            ok=False, final_mp4=None, scene_mp4s=[], thumbs=[], logs=logs
        )

    def get_render_stats(self) -> Dict[str, Any]:
        """Get render orchestrator statistics."""
        stats = {
            "caching_enabled": self.enable_caching,
        }

        if self.cache:
            stats["cache_stats"] = self.cache.get_cache_stats()

        return stats

    def cleanup_cache(self, operation_type: str = None):
        """Clean up cache entries."""
        if self.cache:
            self.cache.clear_cache(operation_type)


def render_video_no_audio(rin: RenderInput) -> RenderResult:
    """
    Main entry point for T6 video rendering pipeline.

    Renders each scene with Manim at target quality (silent),
    applies optional video-only crossfades or straight cuts,
    concatenates to final MP4 (silent), and generates thumbnails.

    Args:
        rin: Complete render input specification

    Returns:
        RenderResult with final video and artifacts
    """
    orchestrator = RenderOrchestrator()
    return orchestrator.render_video(rin)


def render_with_custom_cache(
    rin: RenderInput, cache_dir: Path = None, enable_caching: bool = True
) -> RenderResult:
    """
    Render video with custom cache settings.

    Args:
        rin: Render input
        cache_dir: Custom cache directory
        enable_caching: Whether to enable caching

    Returns:
        RenderResult
    """
    cache = RenderCache(cache_dir=cache_dir) if enable_caching else None
    orchestrator = RenderOrchestrator(cache=cache, enable_caching=enable_caching)
    return orchestrator.render_video(rin)


def batch_render_videos(
    render_inputs: List[RenderInput],
    enable_caching: bool = True,
    max_concurrent: int = 1,
) -> List[RenderResult]:
    """
    Render multiple videos in batch.

    Args:
        render_inputs: List of render inputs
        enable_caching: Whether to enable caching
        max_concurrent: Maximum concurrent renders (currently 1)

    Returns:
        List of RenderResult, one per input
    """
    # Currently sequential processing only
    # Could be enhanced with concurrent processing in the future

    orchestrator = RenderOrchestrator(enable_caching=enable_caching)
    results = []

    for rin in render_inputs:
        result = orchestrator.render_video(rin)
        results.append(result)

        # Early exit on critical failures
        if not result.ok and "timeout" in result.logs.get("error_message", "").lower():
            break

    return results
