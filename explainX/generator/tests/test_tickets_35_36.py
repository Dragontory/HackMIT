"""
Tests for Tickets 3.5 & 3.6 enhancements.

- Ticket 3.5: Deterministic prompt flow with repair agent
- Ticket 3.6: Enhanced style pack integration
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)

# Add the parent directories to the path
sys.path.append(str(Path(__file__).parent.parent))

from agents import CodegenInput, CodegenService, CodegenFailure
from agents.codegen_service import CodegenServiceError
from style.models import StylePack, ColorPalette
from agents.dto import GenerationConstraints


class TestTicket35DeterministicFlow:
    """Test cases for Ticket 3.5 deterministic validation → repair → failure flow."""

    @pytest.fixture
    def valid_style_pack(self):
        """Create a valid style pack for testing."""
        colors = ColorPalette(
            primary_text="#2D3748", accent="#3182CE", background="#F7FAFC"
        )
        return StylePack(version="1.0", name="test_flow", colors=colors)

    @pytest.fixture
    def sample_input(self, valid_style_pack):
        """Create sample codegen input."""
        return CodegenInput(
            video_id="test_flow_001",
            scene_id="deterministic_test",
            section_heading="Test Flow",
            section_text="This is test content for the deterministic flow testing.",
            assets=[],
            style=valid_style_pack,
            constraints={"max_operations": 5},
        )

    def test_validation_success_no_repair_needed(self, sample_input):
        """Test that valid scenes pass without repair."""
        service = CodegenService(use_mock_client=True)

        # Mock validator to return valid on first try
        with patch.object(service.validator, "validate_scene", return_value=(True, [])):
            # Should complete without calling repair service
            output = service.generate_scene_sync(sample_input)

            assert output.scene_json is not None
            assert "scene_id" in output.scene_json
            assert not output.cached  # First generation

    def test_validation_failure_triggers_repair(self, sample_input):
        """Test that CodegenFailure is raised when repair fails."""
        service = CodegenService(use_mock_client=True)

        # Mock validator to always fail (simulating repair failure)
        with patch.object(
            service.validator, "validate_scene", return_value=(False, ["Test error"])
        ):
            # Should raise CodegenFailure when repair fails
            with pytest.raises(CodegenFailure) as exc_info:
                service.generate_scene_sync(sample_input)

            failure = exc_info.value
            assert failure.scene_id == sample_input.scene_id
            assert "Test error" in str(failure.validation_errors)

    def test_repair_failure_raises_codegen_failure(self, sample_input):
        """Test that failed repair raises CodegenFailure exception."""
        service = CodegenService(use_mock_client=True)

        # Mock validator to always fail
        with patch.object(
            service.validator,
            "validate_scene",
            return_value=(False, ["Persistent error"]),
        ):
            # Should raise CodegenFailure
            with pytest.raises(CodegenFailure) as exc_info:
                service.generate_scene_sync(sample_input)

            failure = exc_info.value
            assert failure.scene_id == sample_input.scene_id
            assert failure.section_text == sample_input.section_text
            assert len(failure.validation_errors) > 0

            # Test debug info
            debug_info = failure.get_debug_info()
            assert debug_info["scene_id"] == sample_input.scene_id
            assert "failure_reason" in debug_info

    @pytest.mark.asyncio
    async def test_async_validation_repair_flow(self, sample_input):
        """Test the async version of validation → repair flow."""
        service = CodegenService(use_mock_client=True)

        # Mock successful validation for async flow
        with patch.object(service.validator, "validate_scene", return_value=(True, [])):
            output = await service.generate_scene_async(sample_input)

            assert output.scene_json is not None
            assert "scene_id" in output.scene_json
            assert "timeline" in output.scene_json


class TestTicket36StyleIntegration:
    """Test cases for Ticket 3.6 enhanced style pack integration."""

    @pytest.fixture
    def educational_style_pack(self):
        """Create an educational style pack for testing."""
        colors = ColorPalette(
            primary_text="#111111", accent="#2563EB", background="#FFFFFF"
        )
        return StylePack(
            version="1.0",
            name="edu_clean_v2",
            colors=colors,
            description="Educational style optimized for learning",
        )

    @pytest.fixture
    def dark_contrast_style_pack(self):
        """Create a dark high-contrast style pack."""
        colors = ColorPalette(
            primary_text="#FFFFFF", accent="#00FFAA", background="#000000"
        )
        return StylePack(
            version="1.0",
            name="dark_high_contrast",
            colors=colors,
            description="Dark theme with high contrast for accessibility",
        )

    def test_style_hints_semantic_description(self, educational_style_pack):
        """Test that style hints provide semantic descriptions, not raw values."""
        from agents.prompts import PromptTemplates
        from style.provider import StylePackProvider

        templates = PromptTemplates()
        provider = StylePackProvider(educational_style_pack)

        style_info = templates._format_style_info(provider)

        # Should contain semantic descriptions
        assert "Typography Guidance:" in style_info
        assert "Layout Preferences:" in style_info
        assert "Content Guidance:" in style_info

        # Should not contain raw hex codes in the guidance text
        lines = style_info.split("\n")
        guidance_lines = [line for line in lines if not line.startswith("**")]
        assert not any(
            "#" in line for line in guidance_lines
        ), "Should not expose raw hex codes"

        # Should contain semantic color descriptions
        assert any(
            "contrast" in line.lower() or "theme" in line.lower() for line in lines
        )

        # Should contain emphasis levels, not raw scales
        assert any("emphasis" in line.lower() for line in lines)

    def test_educational_style_preferences(self, educational_style_pack):
        """Test that educational styles get appropriate preferences."""
        from agents.prompts import PromptTemplates
        from style.provider import StylePackProvider

        templates = PromptTemplates()
        provider = StylePackProvider(educational_style_pack)

        # Test 2D preference detection
        assert templates._infer_visual_preference(provider) == True  # Should prefer 2D

        # Test color scheme description
        color_scheme = templates._describe_color_scheme(provider)
        assert "contrast" in color_scheme.lower()

        # Test scale to emphasis conversion
        assert templates._scale_to_emphasis(1.2) == "high emphasis"
        assert templates._scale_to_emphasis(0.8) == "moderate emphasis"

    def test_dark_contrast_style_preferences(self, dark_contrast_style_pack):
        """Test that dark/contrast styles get accessibility preferences."""
        from agents.prompts import PromptTemplates
        from style.provider import StylePackProvider

        templates = PromptTemplates()
        provider = StylePackProvider(dark_contrast_style_pack)

        # Should prefer 2D for accessibility
        assert templates._infer_visual_preference(provider) == True

        # Should detect dark theme
        color_scheme = templates._describe_color_scheme(provider)
        assert "dark theme" in color_scheme.lower()

    def test_style_integration_in_prompts(self, educational_style_pack):
        """Test that style hints are properly integrated into user prompts."""
        from agents.prompts import PromptTemplates, PromptContext
        from style.provider import StylePackProvider

        templates = PromptTemplates()
        provider = StylePackProvider(educational_style_pack)

        context = PromptContext(
            section_heading="Test Integration",
            section_text="Testing style integration in prompts.",
            video_id="test_001",
            scene_id="integration_test",
            assets=[],
            constraints={"max_operations": 5},
            style_provider=provider,
        )

        user_prompt = templates.create_user_prompt(context)

        # Should contain style guidance
        assert "Style Guidance" in user_prompt
        assert educational_style_pack.name in user_prompt

        # Should contain semantic descriptions - looking for style pack name and educational indicators
        assert "edu_clean_v2" in user_prompt.lower()
        assert "educational" in user_prompt.lower() or "learning" in user_prompt.lower()

    def test_no_manim_conversion_in_style_hints(self, educational_style_pack):
        """Test that style hints don't contain Manim-specific conversions."""
        from agents.prompts import PromptTemplates
        from style.provider import StylePackProvider

        templates = PromptTemplates()
        provider = StylePackProvider(educational_style_pack)

        style_info = templates._format_style_info(provider)

        # Should not contain Manim-specific terms
        manim_terms = ["manim", "mobject", "scene.add", "text_mobject", "mathTex"]
        for term in manim_terms:
            assert (
                term.lower() not in style_info.lower()
            ), f"Should not contain Manim term: {term}"

        # Should contain compiler-friendly hints instead
        compiler_friendly = ["compiler", "sizing", "positioning", "hints", "guidance"]
        assert any(term in style_info.lower() for term in compiler_friendly)


class TestIntegratedFlow35And36:
    """Integration tests for both Ticket 3.5 and 3.6 working together."""

    @pytest.fixture
    def style_pack_with_preferences(self):
        """Create a style pack that will trigger specific preferences."""
        colors = ColorPalette(
            primary_text="#2D3748", accent="#3182CE", background="#F7FAFC"
        )
        return StylePack(
            version="1.0",
            name="edu_accessible_clean",  # Name triggers educational + accessibility preferences
            colors=colors,
        )

    def test_end_to_end_with_style_hints_and_repair(self, style_pack_with_preferences):
        """Test complete flow: style hints → generation → validation → repair."""
        constraints = GenerationConstraints(max_operations=3, prefer_2d=True)

        input_data = CodegenInput(
            video_id="integration_test",
            scene_id="full_flow_test",
            section_heading="Newton's First Law",
            section_text="An object at rest stays at rest unless acted upon by a force.",
            assets=[],
            style=style_pack_with_preferences,
            constraints=constraints.to_dict(),
        )

        service = CodegenService(use_mock_client=True)

        # Mock successful validation (no repair needed for this integration test)
        with patch.object(service.validator, "validate_scene", return_value=(True, [])):
            # Should successfully generate with style hints
            output = service.generate_scene_sync(input_data)

            assert output.scene_json is not None
            assert "scene_id" in output.scene_json
            assert "timeline" in output.scene_json

            # Verify that the flow completed (no exceptions)
            assert output.model_name == "mock-gpt-4o"  # Mock client identifier


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
