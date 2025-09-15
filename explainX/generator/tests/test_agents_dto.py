"""
Tests for agent data transfer objects (Ticket 3).
"""

import pytest
import sys
from pathlib import Path

# Add the parent directories to the path
sys.path.append(str(Path(__file__).parent.parent))

from agents.dto import (
    CodegenInput, CodegenOutput, RepairInput, RepairOutput, GenerationConstraints
)
from style.models import StylePack, ColorPalette


class TestCodegenInput:
    """Test cases for CodegenInput DTO."""
    
    @pytest.fixture
    def valid_style_pack(self):
        """Create a valid style pack for testing."""
        colors = ColorPalette(
            primary_text="#111111",
            accent="#2563EB",
            background="#FFFFFF"
        )
        return StylePack(version="1.0", name="test_style", colors=colors)
    
    def test_valid_codegen_input(self, valid_style_pack):
        """Test creation of valid CodegenInput."""
        input_data = CodegenInput(
            video_id="video_123",
            scene_id="scene_001",
            section_heading="Introduction",
            section_text="This is a test section with educational content.",
            assets=["sha256:abc123" + "0" * 58],  # Valid SHA256 format
            style=valid_style_pack,
            constraints={"max_operations": 10, "prefer_2d": True}
        )
        
        assert input_data.video_id == "video_123"
        assert input_data.scene_id == "scene_001"
        assert input_data.section_heading == "Introduction"
        assert len(input_data.assets) == 1
        assert input_data.constraints["max_operations"] == 10
        assert input_data.allow_external is False  # Default value
    
    def test_empty_video_id_raises_error(self, valid_style_pack):
        """Test that empty video_id raises ValueError."""
        with pytest.raises(ValueError, match="video_id cannot be empty"):
            CodegenInput(
                video_id="",
                scene_id="scene_001",
                section_heading="Test",
                section_text="Test content",
                assets=[],
                style=valid_style_pack,
                constraints={}
            )
    
    def test_empty_scene_id_raises_error(self, valid_style_pack):
        """Test that empty scene_id raises ValueError."""
        with pytest.raises(ValueError, match="scene_id cannot be empty"):
            CodegenInput(
                video_id="video_123",
                scene_id="   ",  # Whitespace only
                section_heading="Test",
                section_text="Test content", 
                assets=[],
                style=valid_style_pack,
                constraints={}
            )
    
    def test_empty_section_text_raises_error(self, valid_style_pack):
        """Test that empty section_text raises ValueError."""
        with pytest.raises(ValueError, match="section_text cannot be empty"):
            CodegenInput(
                video_id="video_123",
                scene_id="scene_001",
                section_heading="Test",
                section_text="",
                assets=[],
                style=valid_style_pack,
                constraints={}
            )
    
    def test_invalid_asset_reference_format(self, valid_style_pack):
        """Test that invalid asset reference format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid asset reference format"):
            CodegenInput(
                video_id="video_123",
                scene_id="scene_001", 
                section_heading="Test",
                section_text="Test content",
                assets=["invalid_ref"],
                style=valid_style_pack,
                constraints={}
            )
    
    def test_invalid_asset_reference_length(self, valid_style_pack):
        """Test that invalid asset reference length raises ValueError."""
        with pytest.raises(ValueError, match="Invalid asset reference length"):
            CodegenInput(
                video_id="video_123",
                scene_id="scene_001",
                section_heading="Test", 
                section_text="Test content",
                assets=["sha256:abc"],  # Too short
                style=valid_style_pack,
                constraints={}
            )


class TestCodegenOutput:
    """Test cases for CodegenOutput DTO."""
    
    def test_valid_codegen_output(self):
        """Test creation of valid CodegenOutput."""
        scene_json = {
            "scene_id": "test_scene",
            "timeline": [
                {"op": "title", "text": "Test Title", "pos": "center", "anim": "write"}
            ]
        }
        
        output = CodegenOutput(
            scene_json=scene_json,
            model_name="gpt-4o-2024-08-06",
            tokens_in=150,
            tokens_out=50,
            cached=False,
            generation_time_ms=1200
        )
        
        assert output.scene_json == scene_json
        assert output.model_name == "gpt-4o-2024-08-06"
        assert output.tokens_in == 150
        assert output.tokens_out == 50
        assert output.cached is False
        assert output.generation_time_ms == 1200
    
    def test_empty_scene_json_raises_error(self):
        """Test that empty scene_json raises ValueError."""
        with pytest.raises(ValueError, match="scene_json cannot be empty"):
            CodegenOutput(
                scene_json={},
                model_name="gpt-4o",
                tokens_in=100,
                tokens_out=50,
                cached=False,
                generation_time_ms=1000
            )
    
    def test_negative_tokens_in_raises_error(self):
        """Test that negative tokens_in raises ValueError."""
        with pytest.raises(ValueError, match="tokens_in must be non-negative"):
            CodegenOutput(
                scene_json={"scene_id": "test", "timeline": []},
                model_name="gpt-4o",
                tokens_in=-10,
                tokens_out=50,
                cached=False,
                generation_time_ms=1000
            )
    
    def test_missing_required_scene_keys(self):
        """Test that missing required keys in scene_json raises ValueError."""
        with pytest.raises(ValueError, match="scene_json missing required key: timeline"):
            CodegenOutput(
                scene_json={"scene_id": "test"},  # Missing timeline
                model_name="gpt-4o",
                tokens_in=100,
                tokens_out=50,
                cached=False,
                generation_time_ms=1000
            )


class TestRepairInput:
    """Test cases for RepairInput DTO."""
    
    @pytest.fixture
    def valid_style_pack(self):
        """Create a valid style pack for testing."""
        colors = ColorPalette(
            primary_text="#111111",
            accent="#2563EB", 
            background="#FFFFFF"
        )
        return StylePack(version="1.0", name="repair_test", colors=colors)
    
    def test_valid_repair_input(self, valid_style_pack):
        """Test creation of valid RepairInput."""
        repair_input = RepairInput(
            original_scene_json={"scene_id": "test", "timeline": []},
            validator_errors=[{"message": "Test error", "path": "timeline[0].op"}],
            section_text="Original section text for context",
            style=valid_style_pack,
            max_repair_attempts=2
        )
        
        assert len(repair_input.validator_errors) == 1
        assert repair_input.max_repair_attempts == 2
        assert repair_input.section_text == "Original section text for context"
    
    def test_empty_original_scene_json_raises_error(self, valid_style_pack):
        """Test that empty original_scene_json raises ValueError."""
        with pytest.raises(ValueError, match="original_scene_json cannot be empty"):
            RepairInput(
                original_scene_json={},
                validator_errors=[{"message": "Error"}],
                section_text="Test text",
                style=valid_style_pack
            )
    
    def test_empty_validator_errors_raises_error(self, valid_style_pack):
        """Test that empty validator_errors raises ValueError."""
        with pytest.raises(ValueError, match="validator_errors cannot be empty"):
            RepairInput(
                original_scene_json={"scene_id": "test", "timeline": []},
                validator_errors=[],
                section_text="Test text",
                style=valid_style_pack
            )
    
    def test_zero_max_repair_attempts_raises_error(self, valid_style_pack):
        """Test that zero max_repair_attempts raises ValueError."""
        with pytest.raises(ValueError, match="max_repair_attempts must be at least 1"):
            RepairInput(
                original_scene_json={"scene_id": "test", "timeline": []},
                validator_errors=[{"message": "Error"}],
                section_text="Test text", 
                style=valid_style_pack,
                max_repair_attempts=0
            )


class TestRepairOutput:
    """Test cases for RepairOutput DTO."""
    
    def test_valid_successful_repair_output(self):
        """Test creation of valid successful RepairOutput."""
        repaired_json = {
            "scene_id": "repaired_scene",
            "timeline": [{"op": "title", "text": "Fixed Title", "pos": "center", "anim": "write"}]
        }
        
        output = RepairOutput(
            success=True,
            repaired_scene_json=repaired_json,
            remaining_errors=[],
            repair_attempts_used=2,
            final_model_name="gpt-4o-repair"
        )
        
        assert output.success is True
        assert output.repaired_scene_json == repaired_json
        assert len(output.remaining_errors) == 0
        assert output.repair_attempts_used == 2
    
    def test_valid_failed_repair_output(self):
        """Test creation of valid failed RepairOutput."""
        output = RepairOutput(
            success=False,
            repaired_scene_json=None,
            remaining_errors=[{"message": "Unfixable error", "path": "root"}],
            repair_attempts_used=3,
            final_model_name="gpt-4o-repair"
        )
        
        assert output.success is False
        assert output.repaired_scene_json is None
        assert len(output.remaining_errors) == 1
        assert output.repair_attempts_used == 3
    
    def test_success_true_without_repaired_json_raises_error(self):
        """Test that success=True without repaired_scene_json raises ValueError."""
        with pytest.raises(ValueError, match="repaired_scene_json required when success=True"):
            RepairOutput(
                success=True,
                repaired_scene_json=None,
                remaining_errors=[],
                repair_attempts_used=1,
                final_model_name="gpt-4o"
            )
    
    def test_success_false_with_repaired_json_raises_error(self):
        """Test that success=False with repaired_scene_json raises ValueError."""
        with pytest.raises(ValueError, match="repaired_scene_json should be None when success=False"):
            RepairOutput(
                success=False,
                repaired_scene_json={"scene_id": "test", "timeline": []},
                remaining_errors=[{"message": "Error"}],
                repair_attempts_used=1,
                final_model_name="gpt-4o"
            )


class TestGenerationConstraints:
    """Test cases for GenerationConstraints."""
    
    def test_default_constraints(self):
        """Test default constraint values."""
        constraints = GenerationConstraints()
        
        assert constraints.max_operations == 20
        assert constraints.max_text_length == 160
        assert constraints.max_latex_length == 480
        assert constraints.prefer_2d is True
        assert constraints.require_title is True
        assert constraints.max_pause_duration == 2.0
    
    def test_custom_constraints(self):
        """Test custom constraint values."""
        constraints = GenerationConstraints(
            max_operations=15,
            max_text_length=120,
            prefer_2d=False,
            require_title=False
        )
        
        assert constraints.max_operations == 15
        assert constraints.max_text_length == 120
        assert constraints.prefer_2d is False
        assert constraints.require_title is False
        # Should still have defaults for non-specified values
        assert constraints.max_latex_length == 480
    
    def test_to_dict_conversion(self):
        """Test conversion to dictionary."""
        constraints = GenerationConstraints(max_operations=10, prefer_2d=False)
        constraints_dict = constraints.to_dict()
        
        expected_keys = {
            "max_operations", "max_text_length", "max_latex_length",
            "prefer_2d", "require_title", "max_pause_duration"
        }
        
        assert set(constraints_dict.keys()) == expected_keys
        assert constraints_dict["max_operations"] == 10
        assert constraints_dict["prefer_2d"] is False
        assert isinstance(constraints_dict["max_text_length"], int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
