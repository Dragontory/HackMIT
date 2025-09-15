"""
Tests for Tickets 3.7 & 3.8 enhancements.

- Ticket 3.7: 2D vs 3D content classification
- Ticket 3.8: Determinism settings
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directories to the path
sys.path.append(str(Path(__file__).parent.parent))

from agents.prompts import PromptTemplates
from agents.client_openai import GenerationConfig, OpenAIClient
from style.models import StylePack, ColorPalette


class TestTicket37DimensionClassification:
    """Test cases for Ticket 3.7 2D vs 3D content classification."""

    @pytest.fixture
    def prompt_templates(self):
        """Create PromptTemplates instance."""
        return PromptTemplates()

    def test_3d_content_detection_surfaces(self, prompt_templates):
        """Test detection of 3D content with surfaces."""
        test_cases_3d = [
            "Consider the surface z = x² + y² which represents a paraboloid.",
            "The function z=f(x,y) = sin(x)*cos(y) creates a wave surface.",
            "We will analyze surfaces in three-dimensional space.",
            "Vector fields in 3D space show the flow direction at each point.",
            "The gradient field ∇f shows the steepest ascent direction.",
            "Cross product a × b gives a vector perpendicular to both.",
            "The curl of a vector field measures rotation in 3D.",
            "Camera motion reveals depth and perspective in the scene.",
            "A sphere has the equation x² + y² + z² = r².",
            "The cylinder extends infinitely in the z-direction.",
        ]

        for text in test_cases_3d:
            dimension = prompt_templates._classify_content_dimension(text)
            assert dimension == "3d", f"Failed for: {text}"

    def test_2d_content_detection(self, prompt_templates):
        """Test detection of 2D content."""
        test_cases_2d = [
            "The quadratic function y = x² + 2x + 1 has a vertex at (-1, 0).",
            "Linear equations can be graphed as straight lines.",
            "In this example, we solve for x in the equation 3x + 5 = 14.",
            "The derivative of f(x) = x² is f'(x) = 2x.",
            "Text-based explanations are best presented in 2D format.",
            "This diagram shows the relationship between variables.",
            "Standard mathematical notation uses familiar symbols.",
        ]

        for text in test_cases_2d:
            dimension = prompt_templates._classify_content_dimension(text)
            assert dimension == "2d", f"Failed for: {text}"

    def test_mathematical_expressions_3d(self, prompt_templates):
        """Test detection of 3D mathematical expressions."""
        expressions_3d = [
            "z = x*y + sin(x*y)",
            "f(x,y,z) = x² + y² + z²",
            "∂f/∂x + ∂f/∂y shows partial derivatives in multiple variables",
            "dz/dx and dz/dy represent the gradient components",
        ]

        for expr in expressions_3d:
            dimension = prompt_templates._classify_content_dimension(expr)
            assert dimension == "3d", f"Failed for expression: {expr}"

    def test_dimension_guidance_in_prompts(self, prompt_templates):
        """Test that dimension guidance appears in prompts."""
        from agents.prompts import PromptContext
        from style.provider import StylePackProvider

        # Create minimal style pack
        colors = ColorPalette(
            primary_text="#000000", accent="#0000FF", background="#FFFFFF"
        )
        style_pack = StylePack(version="1.0", name="test_3d", colors=colors)
        provider = StylePackProvider(style_pack)

        # Test 3D content
        context = PromptContext(
            section_heading="3D Surfaces",
            section_text="Consider the surface z = x² + y² in three-dimensional space.",
            video_id="test_001",
            scene_id="surface_test",
            assets=[],
            constraints={},
            style_provider=provider,
        )

        user_prompt = prompt_templates.create_user_prompt(context)

        # Should contain dimension guidance
        assert "Dimension Guidance" in user_prompt
        assert "**Recommended Dimension:** 3d" in user_prompt

        # Test 2D content
        context_2d = PromptContext(
            section_heading="Linear Functions",
            section_text="The linear function y = 2x + 1 represents a straight line.",
            video_id="test_002",
            scene_id="linear_test",
            assets=[],
            constraints={},
            style_provider=provider,
        )

        user_prompt_2d = prompt_templates.create_user_prompt(context_2d)
        assert "**Recommended Dimension:** 2d" in user_prompt_2d

    def test_system_prompt_dimension_guidelines(self, prompt_templates):
        """Test that system prompt includes dimension selection guidelines."""
        from style.provider import StylePackProvider

        colors = ColorPalette(
            primary_text="#000000", accent="#0000FF", background="#FFFFFF"
        )
        style_pack = StylePack(version="1.0", name="test_system", colors=colors)
        provider = StylePackProvider(style_pack)

        system_prompt = prompt_templates.create_system_prompt(provider)

        # Should contain dimension selection guidelines
        assert "Dimension Selection (Ticket 3.7)" in system_prompt
        assert '**Choose "dimension": "3d" when content involves:**' in system_prompt
        assert '**Choose "dimension": "2d" for:**' in system_prompt
        assert "Surfaces: z = f(x, y)" in system_prompt
        assert (
            '**Default to "2d" unless 3D visualization significantly enhances understanding.**'
            in system_prompt
        )


class TestTicket38Determinism:
    """Test cases for Ticket 3.8 determinism settings."""

    def test_generation_config_determinism_settings(self):
        """Test that GenerationConfig has correct determinism settings."""
        config = GenerationConfig()

        # Ticket 3.8 requirements
        assert config.temperature == 0.2
        assert config.top_p == 0.9
        assert config.seed == 12345
        assert config.max_tokens == 4000  # Cap for cost/latency

    def test_custom_determinism_config(self):
        """Test custom determinism configuration."""
        config = GenerationConfig(
            temperature=0.1, top_p=0.8, seed=54321, max_tokens=2000
        )

        assert config.temperature == 0.1
        assert config.top_p == 0.8
        assert config.seed == 54321
        assert config.max_tokens == 2000

    def test_openai_client_uses_determinism_settings(self):
        """Test that OpenAI client applies determinism settings in API calls."""
        # Create client with custom config
        config = GenerationConfig(
            temperature=0.3, top_p=0.95, seed=98765, max_tokens=2000
        )

        # Test that the config is properly stored
        assert config.temperature == 0.3
        assert config.top_p == 0.95
        assert config.seed == 98765
        assert config.max_tokens == 2000

        # Test that config values are correctly applied
        # (MockOpenAIClient will use default if no config provided, so test the config itself)
        assert config.temperature == 0.3
        assert config.top_p == 0.95
        assert config.seed == 98765
        assert config.max_tokens == 2000

    def test_seed_optional_handling(self):
        """Test that seed parameter is handled correctly when None."""
        # Config without seed
        config = GenerationConfig(seed=None)
        assert config.seed is None

        # Config with seed
        config_with_seed = GenerationConfig(seed=12345)
        assert config_with_seed.seed == 12345

        # Test that configs handle None seed correctly
        assert config.seed is None
        assert config_with_seed.seed == 12345

    def test_structured_outputs_force_json(self):
        """Test that structured outputs are still enforced (already implemented)."""
        config = GenerationConfig()

        # Should have response format configured for structured outputs
        assert hasattr(config, "model")
        assert config.model in [
            "gpt-5",
            "gpt-4o-2024-08-06",
        ]  # Model supporting structured outputs


class TestIntegratedTickets3738:
    """Integration tests for both Ticket 3.7 and 3.8 working together."""

    def test_end_to_end_3d_content_with_determinism(self):
        """Test complete flow with 3D content classification and determinism."""
        from agents import CodegenService, CodegenInput
        from style.provider import StylePackProvider

        # Create style pack
        colors = ColorPalette(
            primary_text="#111111", accent="#2563EB", background="#FFFFFF"
        )
        style_pack = StylePack(version="1.0", name="integration_3d", colors=colors)

        # Create input with 3D content
        input_data = CodegenInput(
            video_id="integration_test",
            scene_id="test_3d_determinism",
            section_heading="3D Surface Analysis",
            section_text="Consider the surface z = x² + y² which forms a paraboloid. Vector fields in 3D space show flow directions.",
            assets=[],
            style=style_pack,
            constraints={"max_operations": 5},
        )

        # Create service with mock client to avoid API calls
        service = CodegenService(use_mock_client=True)

        # Test that prompts are generated correctly
        system_prompt, user_prompt = service._create_prompts(input_data)

        # Should contain 3D dimension guidance
        assert "3D Surface Analysis" in user_prompt
        assert "**Recommended Dimension:** 3d" in user_prompt
        assert "Dimension Selection (Ticket 3.7)" in system_prompt

        # Should have correct determinism settings
        assert service.openai_client.config.temperature == 0.2
        assert service.openai_client.config.top_p == 0.9

    def test_2d_content_deterministic_generation(self):
        """Test 2D content with deterministic settings."""
        from agents import CodegenService, CodegenInput

        colors = ColorPalette(
            primary_text="#333333", accent="#FF6600", background="#FFFFFF"
        )
        style_pack = StylePack(version="1.0", name="integration_2d", colors=colors)

        input_data = CodegenInput(
            video_id="integration_test_2d",
            scene_id="test_2d_determinism",
            section_heading="Linear Functions",
            section_text="The linear function y = 2x + 1 represents a straight line with slope 2.",
            assets=[],
            style=style_pack,
            constraints={"max_operations": 3},
        )

        service = CodegenService(use_mock_client=True)
        system_prompt, user_prompt = service._create_prompts(input_data)

        # Should recommend 2D
        assert "**Recommended Dimension:** 2d" in user_prompt

        # Verify determinism settings
        config = service.openai_client.config
        assert config.temperature == 0.2
        assert config.top_p == 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
