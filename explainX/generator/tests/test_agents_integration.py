"""
Integration tests for the Codegen Agent system (Ticket 3).

Tests the complete flow from input to output using the mock client.
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directories to the path
sys.path.append(str(Path(__file__).parent.parent))

from agents import CodegenInput, CodegenOutput, CodegenService
from agents.codegen_service import BatchCodegenService
from style.models import StylePack, ColorPalette
from agents.dto import GenerationConstraints


class TestCodegenServiceIntegration:
    """Integration tests for CodegenService."""

    @pytest.fixture
    def sample_style_pack(self):
        """Create a sample style pack for testing."""
        colors = ColorPalette(
            primary_text="#2D3748", accent="#3182CE", background="#F7FAFC"
        )
        return StylePack(version="1.0", name="test_style", colors=colors)

    @pytest.fixture
    def sample_codegen_input(self, sample_style_pack):
        """Create a sample codegen input."""
        constraints = GenerationConstraints(
            max_operations=10, prefer_2d=True, require_title=True
        )

        return CodegenInput(
            video_id="test_video_123",
            scene_id="test_scene_001",
            section_heading="Introduction to Quadratic Equations",
            section_text="Quadratic equations are polynomial equations of degree two. They have the general form ax² + bx + c = 0, where a, b, and c are constants and a ≠ 0.",
            assets=[],
            style=sample_style_pack,
            constraints=constraints.to_dict(),
            allow_external=False,
        )

    @pytest.fixture
    def mock_codegen_service(self):
        """Create a CodegenService with mock client."""
        return CodegenService(use_mock_client=True)

    def test_synchronous_generation(self, mock_codegen_service, sample_codegen_input):
        """Test synchronous scene generation."""
        # Mock validator to pass validation (new Ticket 3.5 behavior)
        with patch.object(
            mock_codegen_service.validator, "validate_scene", return_value=(True, [])
        ):
            output = mock_codegen_service.generate_scene_sync(sample_codegen_input)

            assert isinstance(output, CodegenOutput)
            assert output.scene_json is not None
            assert "scene_id" in output.scene_json
            assert "timeline" in output.scene_json
            assert output.model_name == "mock-gpt-4o"
            assert output.tokens_in > 0
            assert output.tokens_out > 0
            assert output.generation_time_ms >= 0
            assert output.cached is False

    @pytest.mark.asyncio
    async def test_asynchronous_generation(
        self, mock_codegen_service, sample_codegen_input
    ):
        """Test asynchronous scene generation."""
        # Mock validator to pass validation (new Ticket 3.5 behavior)
        with patch.object(
            mock_codegen_service.validator, "validate_scene", return_value=(True, [])
        ):
            output = await mock_codegen_service.generate_scene_async(
                sample_codegen_input
            )

            assert isinstance(output, CodegenOutput)
            assert output.scene_json is not None
            assert "scene_id" in output.scene_json
            assert "timeline" in output.scene_json
            assert output.model_name == "mock-gpt-4o"
            assert output.cached is False

    def test_caching_behavior(self, mock_codegen_service, sample_codegen_input):
        """Test that caching works correctly."""
        # Mock validator to pass validation (new Ticket 3.5 behavior)
        with patch.object(
            mock_codegen_service.validator, "validate_scene", return_value=(True, [])
        ):
            # First generation should not be cached
            output1 = mock_codegen_service.generate_scene_sync(sample_codegen_input)
            assert output1.cached is False

            # Second identical generation should be cached
            output2 = mock_codegen_service.generate_scene_sync(sample_codegen_input)
            assert output2.cached is True
            assert output2.tokens_in == 0  # No tokens used for cached result
            assert output2.generation_time_ms == 0  # No generation time for cache
            assert output2.model_name == "cached"

    def test_input_validation(self, mock_codegen_service, sample_style_pack):
        """Test input validation catches common issues."""
        # Test very short section text
        short_input = CodegenInput(
            video_id="test",
            scene_id="test",
            section_heading="Test",
            section_text="Hi",  # Too short
            assets=[],
            style=sample_style_pack,
            constraints={},
        )

        errors = mock_codegen_service.validate_input(short_input)
        assert len(errors) > 0
        assert any("too short" in error.lower() for error in errors)

        # Test very long section text
        long_input = CodegenInput(
            video_id="test",
            scene_id="test",
            section_heading="Test",
            section_text="A" * 15000,  # Too long
            assets=[],
            style=sample_style_pack,
            constraints={},
        )

        errors = mock_codegen_service.validate_input(long_input)
        assert len(errors) > 0
        assert any("too long" in error.lower() for error in errors)

    def test_service_status(self, mock_codegen_service):
        """Test service status reporting."""
        status = mock_codegen_service.get_service_status()

        assert isinstance(status, dict)
        assert "openai_rate_limit" in status
        assert "cache_stats" in status
        assert "validator_loaded" in status
        assert "prompts_loaded" in status

        assert status["validator_loaded"] is True
        assert status["prompts_loaded"] is True

    def test_connection_test(self, mock_codegen_service):
        """Test API connection testing."""
        # Mock client should always report successful connection
        assert mock_codegen_service.test_connection() is True


class TestBatchCodegenService:
    """Tests for batch processing functionality."""

    @pytest.fixture
    def sample_style_pack(self):
        """Create a sample style pack for testing."""
        colors = ColorPalette(
            primary_text="#111111", accent="#2563EB", background="#FFFFFF"
        )
        return StylePack(version="1.0", name="batch_test", colors=colors)

    @pytest.fixture
    def batch_inputs(self, sample_style_pack):
        """Create multiple codegen inputs for batch testing."""
        inputs = []
        for i in range(3):
            input_data = CodegenInput(
                video_id=f"batch_video_{i}",
                scene_id=f"batch_scene_{i:03d}",
                section_heading=f"Section {i+1}: Test Topic",
                section_text=f"This is test section {i+1} content for batch processing testing. It contains educational material about topic {i+1}.",
                assets=[],
                style=sample_style_pack,
                constraints={"max_operations": 8, "prefer_2d": True},
            )
            inputs.append(input_data)

        return inputs

    @pytest.fixture
    def batch_service(self):
        """Create a BatchCodegenService with mock client."""
        base_service = CodegenService(use_mock_client=True)
        return BatchCodegenService(base_service, max_concurrent=2)

    @pytest.mark.asyncio
    async def test_async_batch_generation(self, batch_service, batch_inputs):
        """Test asynchronous batch generation."""
        # Mock validator to pass validation (new Ticket 3.5 behavior)
        with patch.object(
            batch_service.base_service.validator,
            "validate_scene",
            return_value=(True, []),
        ):
            outputs = await batch_service.generate_scenes_async(batch_inputs)

            assert len(outputs) == len(batch_inputs)

            for i, output in enumerate(outputs):
                assert isinstance(output, CodegenOutput)
                assert output.scene_json is not None
                assert "timeline" in output.scene_json
                # Should not have errors in mock client
                assert "error" not in output.scene_json

    def test_sync_batch_generation(self, batch_service, batch_inputs):
        """Test synchronous batch generation."""
        outputs = batch_service.generate_scenes_sync(batch_inputs)

        assert len(outputs) == len(batch_inputs)

        for i, output in enumerate(outputs):
            assert isinstance(output, CodegenOutput)
            assert output.scene_json is not None

            # Check that we get valid scene structure
            scene_json = output.scene_json
            assert "timeline" in scene_json
            assert isinstance(scene_json["timeline"], list)

    @pytest.mark.asyncio
    async def test_batch_error_handling(self, batch_inputs):
        """Test batch processing with error conditions."""
        # Create a service that will fail
        base_service = CodegenService(use_mock_client=True)

        # Mock the base service to raise an exception for second input
        def side_effect(input_data):
            if "batch_scene_001" in input_data.scene_id:
                raise Exception("Simulated generation failure")
            # For non-failing inputs, call the real method
            return base_service.generate_scene_sync(input_data)

        with patch.object(
            base_service, "generate_scene_async", side_effect=side_effect
        ):
            batch_service = BatchCodegenService(base_service)
            outputs = await batch_service.generate_scenes_async(batch_inputs)

            assert len(outputs) == len(batch_inputs)

            # Check that failed generation creates error output
            failed_output = outputs[1]  # Second item should fail
            assert "error" in failed_output.scene_json
            assert failed_output.model_name == "error"
            assert (
                "timeline" in failed_output.scene_json
            )  # Should still be valid structure
            assert len(failed_output.scene_json["timeline"]) > 0


class TestCodegenPromptGeneration:
    """Test prompt generation within the codegen service."""

    @pytest.fixture
    def sample_style_pack(self):
        """Create a sample style pack."""
        colors = ColorPalette(
            primary_text="#333333", accent="#FF6B35", background="#FFFFFF"
        )
        return StylePack(
            version="2.0",
            name="prompt_test_style",
            colors=colors,
            description="Style pack for prompt generation testing",
        )

    def test_prompt_creation_with_different_content_types(self, sample_style_pack):
        """Test that different content types generate appropriate prompts."""
        service = CodegenService(use_mock_client=True)

        test_cases = [
            {
                "text": "Solve the quadratic equation x² + 5x + 6 = 0 using the quadratic formula.",
                "expected_type": "math",
            },
            {
                "text": "In this experiment, we will observe the reaction between acid and base to test our hypothesis.",
                "expected_type": "science",
            },
            {
                "text": "For example, consider a car traveling at constant velocity. This demonstrates Newton's first law.",
                "expected_type": "example",
            },
            {
                "text": "In summary, we have covered three main topics: forces, motion, and energy conservation.",
                "expected_type": "summary",
            },
        ]

        for test_case in test_cases:
            input_data = CodegenInput(
                video_id="prompt_test",
                scene_id="prompt_scene",
                section_heading="Test Section",
                section_text=test_case["text"],
                assets=[],
                style=sample_style_pack,
                constraints={},
            )

            # Test that prompt creation doesn't raise errors
            system_prompt, user_prompt = service._create_prompts(input_data)

            assert isinstance(system_prompt, str)
            assert isinstance(user_prompt, str)
            assert len(system_prompt) > 100  # Should be substantial
            assert len(user_prompt) > 100

            # Check that content appears in prompts
            assert test_case["text"] in user_prompt
            assert (
                sample_style_pack.name in system_prompt
                or sample_style_pack.name in user_prompt
            )


class TestCodegenServiceErrorHandling:
    """Test error handling in the codegen service."""

    @pytest.fixture
    def sample_style_pack(self):
        """Create a sample style pack."""
        colors = ColorPalette(
            primary_text="#111111", accent="#2563EB", background="#FFFFFF"
        )
        return StylePack(version="1.0", name="error_test", colors=colors)

    def test_invalid_input_handling(self, sample_style_pack):
        """Test handling of various invalid inputs."""
        service = CodegenService(use_mock_client=True)

        # Test with invalid asset reference
        with pytest.raises(ValueError, match="Invalid asset reference format"):
            CodegenInput(
                video_id="test",
                scene_id="test",
                section_heading="Test",
                section_text="Test content",
                assets=["invalid_asset_ref"],
                style=sample_style_pack,
                constraints={},
            )

    def test_service_initialization_errors(self):
        """Test service initialization with various error conditions."""
        # Test with invalid configuration should still work with mock client
        service = CodegenService(
            use_mock_client=True, cache_file="/invalid/path/that/does/not/exist.cache"
        )

        # Service should still be functional
        assert service.test_connection() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
