"""
T7.4: Extended thumbnails and contact sheet generation.

Provides advanced thumbnail generation capabilities including contact sheets,
poster frames, and evenly distributed frame sampling for video QC.
"""

import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont

from .probe import VideoProbe


@dataclass(frozen=True)
class ThumbnailSpec:
    """Specification for thumbnail generation."""

    timestamp_s: float
    width: int = 320
    height: int = 180
    format: str = "png"  # "png", "jpg"
    quality: int = 95  # For JPEG


@dataclass(frozen=True)
class ContactSheetSpec:
    """Specification for contact sheet generation."""

    grid_cols: int = 3
    grid_rows: int = 3
    frame_width: int = 320
    frame_height: int = 180
    spacing: int = 10
    background_color: str = "#000000"
    text_color: str = "#FFFFFF"
    font_size: int = 12
    show_timestamps: bool = True
    show_video_info: bool = True


@dataclass(frozen=True)
class ThumbnailResult:
    """Result of thumbnail generation operation."""

    success: bool
    output_path: Optional[Path] = None
    timestamp_s: float = 0.0
    width: int = 0
    height: int = 0
    file_size_bytes: int = 0
    generation_time_s: float = 0.0
    error_message: str = ""


class ExtendedThumbnailGenerator:
    """T7.4: Extended thumbnail and contact sheet generator."""

    def __init__(self, timeout_s: int = 60):
        """
        Initialize extended thumbnail generator.

        Args:
            timeout_s: Timeout for FFmpeg operations
        """
        self.timeout_s = timeout_s
        self.probe = VideoProbe()

    def generate_poster_frame(
        self,
        video_path: Path,
        output_path: Path,
        timestamp_s: float = 1.0,
        width: int = 1280,
        height: int = 720,
    ) -> ThumbnailResult:
        """
        Generate a high-quality poster frame.

        Args:
            video_path: Path to video file
            output_path: Output path for poster frame
            timestamp_s: Timestamp to extract (default 1.0s to avoid black frames)
            width: Output width
            height: Output height

        Returns:
            ThumbnailResult with generation details
        """
        import time

        start_time = time.time()

        try:
            # Ensure timestamp is valid
            video_info = self.probe.get_basic_info(video_path)
            duration_s = video_info.get("duration_s", 0)

            if timestamp_s >= duration_s:
                timestamp_s = max(0.1, duration_s - 0.1)

            # Generate poster frame with FFmpeg
            cmd = [
                "ffmpeg",
                "-y",  # Overwrite output
                "-ss",
                str(timestamp_s),
                "-i",
                str(video_path),
                "-frames:v",
                "1",
                "-vf",
                f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black",
                "-q:v",
                "2",  # High quality
                str(output_path),
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.timeout_s, check=True
            )

            generation_time = time.time() - start_time

            if output_path.exists():
                file_size = output_path.stat().st_size

                return ThumbnailResult(
                    success=True,
                    output_path=output_path,
                    timestamp_s=timestamp_s,
                    width=width,
                    height=height,
                    file_size_bytes=file_size,
                    generation_time_s=generation_time,
                )
            else:
                return ThumbnailResult(
                    success=False,
                    error_message="Output file was not created",
                    generation_time_s=generation_time,
                )

        except subprocess.TimeoutExpired:
            return ThumbnailResult(
                success=False,
                error_message=f"FFmpeg timeout after {self.timeout_s}s",
                generation_time_s=time.time() - start_time,
            )
        except subprocess.CalledProcessError as e:
            return ThumbnailResult(
                success=False,
                error_message=f"FFmpeg failed: {e.stderr}",
                generation_time_s=time.time() - start_time,
            )
        except Exception as e:
            return ThumbnailResult(
                success=False,
                error_message=f"Generation failed: {str(e)}",
                generation_time_s=time.time() - start_time,
            )

    def generate_midpoint_frame(
        self,
        video_path: Path,
        output_path: Path,
        width: int = 640,
        height: int = 360,
    ) -> ThumbnailResult:
        """
        Generate a midpoint frame thumbnail.

        Args:
            video_path: Path to video file
            output_path: Output path for thumbnail
            width: Output width
            height: Output height

        Returns:
            ThumbnailResult with generation details
        """
        try:
            # Get video duration and calculate midpoint
            video_info = self.probe.get_basic_info(video_path)
            duration_s = video_info.get("duration_s", 0)
            midpoint_s = duration_s / 2.0

            return self.generate_poster_frame(
                video_path=video_path,
                output_path=output_path,
                timestamp_s=midpoint_s,
                width=width,
                height=height,
            )

        except Exception as e:
            return ThumbnailResult(
                success=False,
                error_message=f"Midpoint calculation failed: {str(e)}",
            )

    def generate_evenly_spaced_frames(
        self,
        video_path: Path,
        output_dir: Path,
        frame_count: int = 9,
        frame_spec: ThumbnailSpec = None,
    ) -> List[ThumbnailResult]:
        """
        Generate evenly spaced frames throughout the video.

        Args:
            video_path: Path to video file
            output_dir: Directory for output frames
            frame_count: Number of frames to extract
            frame_spec: Specification for frame generation

        Returns:
            List of ThumbnailResult for each frame
        """
        if frame_spec is None:
            frame_spec = ThumbnailSpec(timestamp_s=0.0)

        results = []

        try:
            # Get video duration
            video_info = self.probe.get_basic_info(video_path)
            duration_s = video_info.get("duration_s", 0)

            if duration_s <= 0:
                return [
                    ThumbnailResult(
                        success=False, error_message="Invalid video duration"
                    )
                ]

            # Calculate timestamps
            timestamps = []
            if frame_count == 1:
                timestamps = [duration_s / 2.0]  # Single midpoint frame
            else:
                # Evenly distribute frames, avoiding very start and end
                start_offset = max(0.1, duration_s * 0.05)  # 5% from start or 0.1s
                end_offset = max(0.1, duration_s * 0.05)  # 5% from end or 0.1s

                if duration_s <= start_offset + end_offset:
                    timestamps = [
                        duration_s / 2.0
                    ]  # Fallback to midpoint for very short videos
                else:
                    usable_duration = duration_s - start_offset - end_offset
                    interval = (
                        usable_duration / (frame_count - 1) if frame_count > 1 else 0
                    )

                    for i in range(frame_count):
                        timestamp = start_offset + (i * interval)
                        timestamps.append(timestamp)

            # Generate frames
            output_dir.mkdir(parents=True, exist_ok=True)

            for i, timestamp in enumerate(timestamps):
                output_path = output_dir / f"frame_{i+1:02d}.{frame_spec.format}"

                result = self.generate_poster_frame(
                    video_path=video_path,
                    output_path=output_path,
                    timestamp_s=timestamp,
                    width=frame_spec.width,
                    height=frame_spec.height,
                )

                results.append(result)

        except Exception as e:
            results.append(
                ThumbnailResult(
                    success=False,
                    error_message=f"Frame extraction failed: {str(e)}",
                )
            )

        return results

    def create_contact_sheet(
        self,
        video_path: Path,
        output_path: Path,
        spec: ContactSheetSpec = None,
    ) -> ThumbnailResult:
        """
        Create a contact sheet with evenly distributed frames.

        Args:
            video_path: Path to video file
            output_path: Output path for contact sheet
            spec: Contact sheet specification

        Returns:
            ThumbnailResult with generation details
        """
        import time

        start_time = time.time()

        if spec is None:
            spec = ContactSheetSpec()

        try:
            # Calculate total frames needed
            total_frames = spec.grid_cols * spec.grid_rows

            # Create temporary directory for individual frames
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Generate individual frames
                frame_spec = ThumbnailSpec(
                    timestamp_s=0.0,
                    width=spec.frame_width,
                    height=spec.frame_height,
                    format="png",
                )

                frame_results = self.generate_evenly_spaced_frames(
                    video_path=video_path,
                    output_dir=temp_path,
                    frame_count=total_frames,
                    frame_spec=frame_spec,
                )

                # Filter successful frames
                successful_frames = [
                    r for r in frame_results if r.success and r.output_path
                ]

                if not successful_frames:
                    return ThumbnailResult(
                        success=False,
                        error_message="No frames could be extracted",
                        generation_time_s=time.time() - start_time,
                    )

                # Create contact sheet image
                contact_sheet = self._create_contact_sheet_image(
                    frame_paths=[r.output_path for r in successful_frames],
                    spec=spec,
                    video_path=video_path,
                )

                # Save contact sheet
                output_path.parent.mkdir(parents=True, exist_ok=True)
                contact_sheet.save(output_path, "PNG", quality=95)

                generation_time = time.time() - start_time
                file_size = output_path.stat().st_size

                return ThumbnailResult(
                    success=True,
                    output_path=output_path,
                    width=contact_sheet.width,
                    height=contact_sheet.height,
                    file_size_bytes=file_size,
                    generation_time_s=generation_time,
                )

        except Exception as e:
            return ThumbnailResult(
                success=False,
                error_message=f"Contact sheet creation failed: {str(e)}",
                generation_time_s=time.time() - start_time,
            )

    def _create_contact_sheet_image(
        self,
        frame_paths: List[Path],
        spec: ContactSheetSpec,
        video_path: Path,
    ) -> Image.Image:
        """Create contact sheet image from individual frames."""
        # Calculate contact sheet dimensions
        sheet_width = (spec.frame_width * spec.grid_cols) + (
            spec.spacing * (spec.grid_cols + 1)
        )

        # Add space for video info header
        header_height = 60 if spec.show_video_info else 0
        grid_height = (spec.frame_height * spec.grid_rows) + (
            spec.spacing * (spec.grid_rows + 1)
        )
        sheet_height = header_height + grid_height

        # Create background image
        contact_sheet = Image.new(
            "RGB", (sheet_width, sheet_height), spec.background_color
        )
        draw = ImageDraw.Draw(contact_sheet)

        # Try to load a font (fallback to default if not available)
        try:
            font = ImageFont.truetype("arial.ttf", spec.font_size)
        except:
            try:
                font = ImageFont.load_default()
            except:
                font = None

        # Add video info header
        y_offset = 0
        if spec.show_video_info:
            try:
                video_info = self.probe.get_basic_info(video_path)
                info_text = (
                    f"Video: {video_path.name} | "
                    f"Duration: {video_info.get('duration_s', 0):.1f}s | "
                    f"Resolution: {video_info.get('resolution', 'unknown')} | "
                    f"FPS: {video_info.get('fps', 0):.1f}"
                )

                if font:
                    draw.text(
                        (spec.spacing, spec.spacing),
                        info_text,
                        fill=spec.text_color,
                        font=font,
                    )
                else:
                    draw.text(
                        (spec.spacing, spec.spacing), info_text, fill=spec.text_color
                    )

            except Exception:
                pass  # Skip video info if it fails

            y_offset = header_height

        # Place frames in grid
        for i, frame_path in enumerate(frame_paths[: spec.grid_cols * spec.grid_rows]):
            if not frame_path.exists():
                continue

            try:
                # Calculate grid position
                col = i % spec.grid_cols
                row = i // spec.grid_cols

                x = spec.spacing + (col * (spec.frame_width + spec.spacing))
                y = y_offset + spec.spacing + (row * (spec.frame_height + spec.spacing))

                # Load and paste frame
                frame_img = Image.open(frame_path)
                frame_img = frame_img.resize(
                    (spec.frame_width, spec.frame_height), Image.LANCZOS
                )
                contact_sheet.paste(frame_img, (x, y))

                # Add timestamp if requested
                if spec.show_timestamps:
                    # Calculate timestamp for this frame
                    try:
                        video_info = self.probe.get_basic_info(video_path)
                        duration_s = video_info.get("duration_s", 0)

                        if duration_s > 0:
                            timestamp_s = (
                                i / max(1, len(frame_paths) - 1)
                            ) * duration_s
                            timestamp_text = f"{timestamp_s:.1f}s"

                            # Draw timestamp with background
                            if font:
                                text_bbox = draw.textbbox(
                                    (0, 0), timestamp_text, font=font
                                )
                                text_width = text_bbox[2] - text_bbox[0]
                                text_height = text_bbox[3] - text_bbox[1]
                            else:
                                text_width, text_height = (
                                    40,
                                    12,
                                )  # Approximate default font size

                            timestamp_x = x + spec.frame_width - text_width - 5
                            timestamp_y = y + spec.frame_height - text_height - 5

                            # Draw background rectangle
                            draw.rectangle(
                                [
                                    timestamp_x - 2,
                                    timestamp_y - 2,
                                    timestamp_x + text_width + 2,
                                    timestamp_y + text_height + 2,
                                ],
                                fill="#000000",
                            )

                            # Draw timestamp text
                            if font:
                                draw.text(
                                    (timestamp_x, timestamp_y),
                                    timestamp_text,
                                    fill=spec.text_color,
                                    font=font,
                                )
                            else:
                                draw.text(
                                    (timestamp_x, timestamp_y),
                                    timestamp_text,
                                    fill=spec.text_color,
                                )

                    except Exception:
                        pass  # Skip timestamp if calculation fails

            except Exception:
                # Skip this frame if it fails to load
                continue

        return contact_sheet

    def generate_standard_thumbnails(
        self,
        video_path: Path,
        output_dir: Path,
        video_name: str,
    ) -> List[ThumbnailResult]:
        """
        Generate standard set of thumbnails for QC.

        Args:
            video_path: Path to video file
            output_dir: Output directory
            video_name: Base name for thumbnails

        Returns:
            List of ThumbnailResult for all generated thumbnails
        """
        results = []
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate poster frame (high quality)
        poster_result = self.generate_poster_frame(
            video_path=video_path,
            output_path=output_dir / f"{video_name}_poster.png",
            timestamp_s=1.0,
            width=1280,
            height=720,
        )
        results.append(poster_result)

        # Generate midpoint frame
        mid_result = self.generate_midpoint_frame(
            video_path=video_path,
            output_path=output_dir / f"{video_name}_midpoint.png",
            width=640,
            height=360,
        )
        results.append(mid_result)

        # Generate contact sheet
        contact_result = self.create_contact_sheet(
            video_path=video_path,
            output_path=output_dir / f"{video_name}_contact_sheet.png",
        )
        results.append(contact_result)

        return results


def generate_qc_thumbnails(
    video_path: Path,
    output_dir: Path,
    video_name: str,
) -> List[ThumbnailResult]:
    """
    Convenience function to generate QC thumbnails.

    Args:
        video_path: Path to video file
        output_dir: Output directory
        video_name: Base name for thumbnails

    Returns:
        List of ThumbnailResult
    """
    generator = ExtendedThumbnailGenerator()
    return generator.generate_standard_thumbnails(video_path, output_dir, video_name)


def create_video_contact_sheet(
    video_path: Path,
    output_path: Path,
    grid_size: Tuple[int, int] = (3, 3),
) -> ThumbnailResult:
    """
    Convenience function to create contact sheet.

    Args:
        video_path: Path to video file
        output_path: Output path for contact sheet
        grid_size: (columns, rows) for grid

    Returns:
        ThumbnailResult with generation details
    """
    generator = ExtendedThumbnailGenerator()
    spec = ContactSheetSpec(grid_cols=grid_size[0], grid_rows=grid_size[1])
    return generator.create_contact_sheet(video_path, output_path, spec)
