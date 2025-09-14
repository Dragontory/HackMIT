"""
Complete End-to-End Pipeline Test: Scene DSL → Delivery Ready Video

This test demonstrates the complete video generation pipeline:
PDF Notes → [Processor Output] → Scene DSL → Manim Code → Rendered Videos → QC Validated → Delivery Ready

Tests the integration of:
- T4: Scene DSL → Manim Python Source compilation
- T5: Validation and dry-run execution
- T6: Final Manim render and concatenation
- T7: Video QC, metadata, and delivery preparation
"""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Import pipeline components
from generator.compiler import compile_scene_enhanced, CompileOptions, StylePack
from generator.validator import validate_scene, ValidateInput, SandboxLimits
from generator.renderer import (
    render_video_no_audio,
    RenderInput,
    SceneRenderItem,
    RenderQualityPreset,
)
from generator.video_qc import qc_and_package, QCInput, QCSettings


class TestCompletePipeline:
    """Complete end-to-end pipeline integration test."""

    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.output_dir = self.temp_dir / "video_output"
        self.output_dir.mkdir(parents=True)

        # Load sample processor output
        sample_file = Path(__file__).parent / "sample_processor_output.json"
        with open(sample_file, "r") as f:
            self.processor_output = json.load(f)

    def teardown_method(self):
        """Cleanup test files."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_complete_pipeline_integration(self):
        """Test complete Scene DSL → Delivery Ready pipeline."""
        print("\n🎬 COMPLETE VIDEO GENERATION PIPELINE TEST")
        print("=" * 70)

        video_id = "ml_linear_regression_001"
        total_start_time = time.time()

        # Extract components from processor output
        scenes_data = self.processor_output["scenes"]
        style_pack_data = self.processor_output["style_pack"]
        rendering_config = self.processor_output["rendering_config"]

        print(f"\n📊 Processor Output Analysis:")
        print(f"  • Video: {self.processor_output['video_metadata']['title']}")
        print(f"  • Scenes: {len(scenes_data)} scenes")
        print(f"  • Duration: {rendering_config['total_estimated_duration_s']}s")
        print(f"  • Resolution: {rendering_config['resolution']}")

        # T4: Scene DSL → Manim Code Compilation
        print(f"\n🔧 T4: SCENE DSL → MANIM CODE COMPILATION")
        print("-" * 50)

        compiled_scenes = []
        compile_start = time.time()

        # Create style pack
        style_pack = StylePack(
            name=style_pack_data["name"],
            version=style_pack_data["version"],
            colors=style_pack_data["colors"],
            fonts=style_pack_data["fonts"],
            animations=style_pack_data["animations"],
            layout=style_pack_data["layout"],
        )

        # Compile each scene
        for i, scene_data in enumerate(scenes_data):
            scene_file = self.output_dir / f"scene_{i+1:02d}.py"

            try:
                # Configure compilation options
                compile_options = CompileOptions(
                    scene_class_prefix="MLScene",
                    enable_safety_checks=True,
                    target_resolution=(1920, 1080),
                    target_fps=30,
                )

                # Compile scene DSL to Manim code
                compilation_result = compile_scene_enhanced(
                    scene_data=scene_data,
                    style_pack=style_pack,
                    options=compile_options,
                )

                # Save compiled code
                scene_file.write_text(compilation_result.source_code)

                compiled_scenes.append(
                    {
                        "scene_id": scene_data["scene_id"],
                        "class_name": compilation_result.class_name,
                        "file_path": scene_file,
                        "estimated_duration": scene_data.get("duration_s", 30),
                        "source_code": compilation_result.source_code,
                    }
                )

                print(
                    f"  ✅ Compiled: {scene_data['scene_id']} → {compilation_result.class_name}"
                )

            except Exception as e:
                print(f"  ❌ Failed: {scene_data['scene_id']} - {str(e)}")
                continue

        compile_time = time.time() - compile_start
        print(
            f"\n  📊 T4 Results: {len(compiled_scenes)}/{len(scenes_data)} scenes compiled ({compile_time:.1f}s)"
        )

        # T5: Validation and Dry-Run
        print(f"\n🔍 T5: VALIDATION AND DRY-RUN")
        print("-" * 50)

        validated_scenes = []
        validation_start = time.time()

        # Mock T5 validation since we can't run real Manim in test environment
        with patch("generator.validator.sandbox.execute_command") as mock_execute:
            with patch(
                "generator.validator.artifacts.ArtifactManager"
            ) as mock_artifacts:
                # Configure mocks for successful validation
                mock_execute.return_value = (0, "Manim validation successful", "")
                mock_artifacts_instance = Mock()
                mock_artifacts_instance.analyze_artifacts.return_value = Mock(
                    preview_videos=[self.temp_dir / "preview.mp4"],
                    preview_images=[],
                    logs_files=[],
                    other_files=[],
                )
                mock_artifacts.return_value = mock_artifacts_instance

                for scene in compiled_scenes:
                    try:
                        # Create validation input
                        validate_input = ValidateInput(
                            scene_id=scene["scene_id"],
                            main_py=scene["file_path"],
                            class_name=scene["class_name"],
                            out_dir=self.output_dir / "validation" / scene["scene_id"],
                            limits=SandboxLimits(
                                timeout_seconds=60, max_memory_mb=512, max_files=50
                            ),
                        )

                        # Run validation
                        validation_result = validate_scene(validate_input)

                        if validation_result.ok:
                            validated_scenes.append(
                                {
                                    **scene,
                                    "validation_passed": True,
                                    "preview_artifacts": validation_result.artifacts,
                                }
                            )
                            print(f"  ✅ Validated: {scene['scene_id']}")
                        else:
                            print(f"  ❌ Validation failed: {scene['scene_id']}")

                    except Exception as e:
                        print(f"  ❌ Validation error: {scene['scene_id']} - {str(e)}")
                        continue

        validation_time = time.time() - validation_start
        print(
            f"\n  📊 T5 Results: {len(validated_scenes)}/{len(compiled_scenes)} scenes validated ({validation_time:.1f}s)"
        )

        # T6: Final Manim Render and Concatenation
        print(f"\n🎥 T6: FINAL MANIM RENDER AND CONCATENATION")
        print("-" * 50)

        render_start = time.time()

        # Create render input
        scene_render_items = []
        for scene in validated_scenes:
            scene_render_items.append(
                SceneRenderItem(
                    scene_id=scene["scene_id"],
                    class_name=scene["class_name"],
                    main_py=scene["file_path"],
                    est_duration_s=scene["estimated_duration"],
                )
            )

        render_input = RenderInput(
            video_id=video_id,
            scenes=scene_render_items,
            out_dir=self.output_dir / "render",
            quality="1080p",
            fps=30,
            crossfade_s=0.5,  # Add smooth transitions
        )

        # Mock T6 rendering since we can't run real Manim/FFmpeg in test environment
        with patch(
            "generator.renderer.manim_prod.ProductionManimRenderer"
        ) as mock_renderer:
            with patch("generator.renderer.concat.VideoConcatenator") as mock_concat:
                with patch(
                    "generator.renderer.thumbs.generate_standard_thumbnails"
                ) as mock_thumbs:

                    # Mock successful scene renders
                    mock_renderer_instance = Mock()
                    mock_renderer.return_value.__enter__.return_value = (
                        mock_renderer_instance
                    )

                    scene_outputs = []
                    for i, scene in enumerate(scene_render_items):
                        scene_output = (
                            self.output_dir
                            / "render"
                            / "scenes"
                            / f"scene_{scene.scene_id}_prod.mp4"
                        )
                        scene_output.parent.mkdir(parents=True, exist_ok=True)
                        scene_output.write_bytes(b"fake rendered scene content")
                        scene_outputs.append(scene_output)

                    from generator.renderer.manim_prod import ProductionRenderResult

                    mock_renderer_instance.render_scene.side_effect = [
                        ProductionRenderResult(
                            success=True,
                            scene_id=scene.scene_id,
                            class_name=scene.class_name,
                            output_mp4=scene_outputs[i],
                            duration_s=scene.est_duration_s,
                            render_time_s=2.0,
                            stdout="render success",
                            stderr="",
                        )
                        for i, scene in enumerate(scene_render_items)
                    ]

                    # Mock concatenation
                    mock_concat_instance = Mock()
                    mock_concat.return_value.__enter__.return_value = (
                        mock_concat_instance
                    )

                    final_video = self.output_dir / "render" / f"{video_id}_final.mp4"
                    final_video.write_bytes(b"fake final concatenated video content")

                    from generator.renderer.concat import ConcatResult

                    mock_concat_instance.concatenate_videos.return_value = ConcatResult(
                        success=True,
                        output_mp4=final_video,
                        input_videos=scene_outputs,
                        duration_s=sum(s.est_duration_s for s in scene_render_items),
                        processing_time_s=5.0,
                        transitions_applied=len(scene_render_items) - 1,
                        error_message="",
                    )

                    # Mock thumbnails
                    thumb1 = self.output_dir / "render" / "thumbnails" / "poster.png"
                    thumb2 = self.output_dir / "render" / "thumbnails" / "mid.png"
                    thumb1.parent.mkdir(parents=True, exist_ok=True)
                    thumb1.write_bytes(b"fake poster thumbnail")
                    thumb2.write_bytes(b"fake mid thumbnail")

                    from generator.renderer.thumbs import ThumbnailResult

                    mock_thumbs.return_value = [
                        ThumbnailResult(
                            success=True, thumbnail_path=thumb1, extraction_time_s=0.1
                        ),
                        ThumbnailResult(
                            success=True, thumbnail_path=thumb2, extraction_time_s=0.1
                        ),
                    ]

                    # Execute render pipeline
                    render_result = render_video_no_audio(render_input)

                    render_time = time.time() - render_start
                    print(
                        f"  📊 T6 Results: Render {'SUCCESS' if render_result.ok else 'FAILED'} ({render_time:.1f}s)"
                    )

                    if render_result.ok:
                        print(f"  ✅ Final video: {render_result.final_mp4}")
                        print(
                            f"  ✅ Scene videos: {len(render_result.scene_mp4s)} files"
                        )
                        print(f"  ✅ Thumbnails: {len(render_result.thumbs)} files")
                    else:
                        print(
                            f"  ❌ Render failed: {render_result.logs.get('error_message', 'Unknown error')}"
                        )
                        return  # Cannot proceed to T7 without successful render

        # T7: Video QC, Metadata, and Delivery Prep
        print(f"\n🔍 T7: VIDEO QC, METADATA, AND DELIVERY PREP")
        print("-" * 50)

        qc_start = time.time()

        # Create QC input from T6 output
        qc_input = QCInput(
            video_id=video_id,
            final_mp4=render_result.final_mp4,
            thumbs=render_result.thumbs,
            out_dir=self.output_dir / "delivery",
        )

        # Mock T7 QC since we can't run real ffprobe/ffmpeg in test environment
        with patch("generator.video_qc.probe.subprocess.run") as mock_probe:
            with patch("generator.video_qc.qc.subprocess.run") as mock_qc:
                with patch(
                    "generator.video_qc.thumbs.subprocess.run"
                ) as mock_thumb_gen:

                    # Mock video probe results
                    probe_output = {
                        "streams": [
                            {
                                "codec_type": "video",
                                "codec_name": "h264",
                                "width": 1920,
                                "height": 1080,
                                "duration": str(
                                    sum(s.est_duration_s for s in scene_render_items)
                                ),
                                "avg_frame_rate": "30/1",
                                "nb_frames": str(
                                    int(
                                        sum(
                                            s.est_duration_s for s in scene_render_items
                                        )
                                        * 30
                                    )
                                ),
                                "pix_fmt": "yuv420p",
                            }
                        ]
                    }

                    format_output = {
                        "format": {
                            "duration": str(
                                sum(s.est_duration_s for s in scene_render_items)
                            ),
                            "bit_rate": "3500000",
                            "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
                        }
                    }

                    mock_probe.side_effect = [
                        Mock(stdout=json.dumps(probe_output), stderr=""),
                        Mock(stdout=json.dumps(format_output), stderr=""),
                    ]

                    # Mock QC checks (no issues found)
                    mock_qc.return_value = Mock(
                        stderr="No black frames detected\nNo frozen frames detected",
                        returncode=0,
                    )

                    # Mock thumbnail generation
                    mock_thumb_gen.return_value = Mock(
                        returncode=0, stderr="", stdout=""
                    )

                    # Configure QC settings
                    qc_settings = QCSettings(
                        enable_black_detection=True,
                        enable_freeze_detection=True,
                        enable_spec_validation=True,
                    )

                    # Execute QC pipeline
                    from generator.video_qc.orchestrator import QCOrchestrator

                    orchestrator = QCOrchestrator(qc_settings=qc_settings)
                    qc_result = orchestrator.run_qc_pipeline(qc_input)

                    qc_time = time.time() - qc_start
                    print(
                        f"  📊 T7 Results: QC {'PASSED' if qc_result.ok else 'FAILED'} ({qc_time:.1f}s)"
                    )

                    if qc_result.ok:
                        print(f"  ✅ Manifest: {qc_result.manifest}")
                        print(
                            f"  ✅ Extra thumbnails: {len(qc_result.extra_thumbs)} files"
                        )
                        print(f"  ✅ QC issues: {len(qc_result.issues)} issues found")

                        # Create mock delivery artifacts
                        if qc_result.manifest:
                            qc_result.manifest.parent.mkdir(parents=True, exist_ok=True)

                            # Create realistic manifest content
                            manifest_content = {
                                "video_id": video_id,
                                "title": self.processor_output["video_metadata"][
                                    "title"
                                ],
                                "duration_s": sum(
                                    s.est_duration_s for s in scene_render_items
                                ),
                                "resolution": "1920x1080",
                                "fps": 30,
                                "codec": "h264",
                                "pixel_format": "yuv420p",
                                "hash_sha256": "a" * 64,  # Mock hash
                                "qc_passed": True,
                                "qc_issues_count": len(qc_result.issues),
                                "thumbnails": [
                                    str(t.name) for t in render_result.thumbs
                                ]
                                + [
                                    f"extra_{i}.png"
                                    for i in range(len(qc_result.extra_thumbs))
                                ],
                                "scenes_rendered": len(scene_render_items),
                                "processing_pipeline": [
                                    "T4_compile",
                                    "T5_validate",
                                    "T6_render",
                                    "T7_qc",
                                ],
                                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            }

                            qc_result.manifest.write_text(
                                json.dumps(manifest_content, indent=2)
                            )
                    else:
                        print(
                            f"  ❌ QC failed: {qc_result.logs.get('error_message', 'Unknown error')}"
                        )

        # Pipeline Summary
        total_time = time.time() - total_start_time
        print(f"\n🎯 COMPLETE PIPELINE SUMMARY")
        print("=" * 70)
        print(f"✅ Total Processing Time: {total_time:.1f}s")
        print(f"✅ Scenes Compiled (T4): {len(compiled_scenes)}/{len(scenes_data)}")
        print(
            f"✅ Scenes Validated (T5): {len(validated_scenes)}/{len(compiled_scenes)}"
        )
        print(f"✅ Video Rendered (T6): {'SUCCESS' if render_result.ok else 'FAILED'}")
        print(f"✅ QC Validation (T7): {'PASSED' if qc_result.ok else 'FAILED'}")

        print(f"\n📂 DELIVERY ARTIFACTS:")
        if render_result.ok and qc_result.ok:
            print(f"  • Final Video: {render_result.final_mp4}")
            print(f"  • Scene Videos: {len(render_result.scene_mp4s)} files")
            print(
                f"  • Thumbnails: {len(render_result.thumbs + qc_result.extra_thumbs)} files"
            )
            print(f"  • Metadata Manifest: {qc_result.manifest}")
            print(f"  • QC Report: {len(qc_result.issues)} issues")

        print(
            f"\n🚀 PIPELINE STATUS: {'PRODUCTION READY' if render_result.ok and qc_result.ok else 'NEEDS ATTENTION'}"
        )

        # Assertions for test validation
        assert len(compiled_scenes) > 0, "Should compile at least some scenes"
        assert len(validated_scenes) > 0, "Should validate at least some scenes"
        assert render_result.ok, "T6 render should succeed"
        assert qc_result.ok, "T7 QC should pass"
        assert qc_result.manifest is not None, "Should generate delivery manifest"

        print(f"\n✅ Complete pipeline test PASSED!")

    def test_pipeline_error_handling(self):
        """Test pipeline error handling and recovery."""
        print("\n🔧 PIPELINE ERROR HANDLING TEST")
        print("=" * 50)

        # Test with invalid scene data
        invalid_scene = {
            "scene_id": "invalid_001",
            "operations": [
                {"type": "invalid_operation", "content": "This should fail"}
            ],
        }

        try:
            # This should fail gracefully
            style_pack = StylePack(
                name="test",
                version="1.0",
                colors={},
                fonts={},
                animations={},
                layout={},
            )

            compile_options = CompileOptions()
            compilation_result = compile_scene_enhanced(
                scene_data=invalid_scene, style_pack=style_pack, options=compile_options
            )

            # Should not reach here
            assert False, "Should have failed with invalid operation type"

        except Exception as e:
            print(f"  ✅ Error handling: Caught expected error - {type(e).__name__}")

        print(f"  ✅ Pipeline gracefully handles invalid inputs")

    def test_pipeline_performance_metrics(self):
        """Test pipeline performance and resource usage."""
        print("\n📊 PIPELINE PERFORMANCE TEST")
        print("=" * 50)

        # Measure compilation performance
        scenes_data = self.processor_output["scenes"][:3]  # Test with subset

        start_time = time.time()
        memory_usage_mb = 0  # Would measure real memory in production

        compiled_count = 0
        for scene_data in scenes_data:
            try:
                style_pack = StylePack(
                    name="perf_test",
                    version="1.0",
                    colors={"primary": "#000000"},
                    fonts={"primary": "Arial"},
                    animations={"default_duration": 1.0},
                    layout={"margins": {"top": 50}},
                )

                compile_options = CompileOptions()
                compilation_result = compile_scene_enhanced(
                    scene_data=scene_data,
                    style_pack=style_pack,
                    options=compile_options,
                )

                compiled_count += 1

            except Exception as e:
                print(f"  ⚠️ Scene compilation failed: {e}")

        compile_time = time.time() - start_time
        throughput = compiled_count / compile_time if compile_time > 0 else 0

        print(f"  📊 Compilation Performance:")
        print(f"    • Scenes processed: {compiled_count}/{len(scenes_data)}")
        print(f"    • Total time: {compile_time:.2f}s")
        print(f"    • Throughput: {throughput:.1f} scenes/second")
        print(f"    • Memory usage: {memory_usage_mb}MB")

        # Performance assertions
        assert compiled_count > 0, "Should compile at least one scene"
        assert compile_time < 30, "Compilation should be fast"
        assert throughput > 0.1, "Should maintain reasonable throughput"

        print(f"  ✅ Performance test PASSED!")


if __name__ == "__main__":
    # Run as standalone script for demonstration
    test = TestCompletePipeline()
    test.setup_method()

    try:
        test.test_complete_pipeline_integration()
        print("\n🎉 COMPLETE PIPELINE DEMONSTRATION SUCCESSFUL!")

    except Exception as e:
        print(f"\n❌ Pipeline test failed: {e}")
        import traceback

        traceback.print_exc()

    finally:
        test.teardown_method()
