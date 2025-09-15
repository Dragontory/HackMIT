"""
Tests for agent schema tools (Ticket 3).
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import mock_open, patch

# Add the parent directories to the path
sys.path.append(str(Path(__file__).parent.parent))

import agents.schema_tools as schema_tools
from agents.schema_tools import (
    SchemaToolsError,
    load_scene_dsl_schema,
    convert_to_openai_schema,
    create_openai_format_spec,
    validate_openai_compatibility,
    get_operation_schemas,
    create_operation_examples
)


class TestLoadSceneDslSchema:
    """Test cases for loading Scene DSL schema."""
    
    def test_load_existing_schema(self):
        """Test loading the actual Scene DSL schema file."""
        try:
            schema = load_scene_dsl_schema()
            
            # Verify it's a valid schema structure
            assert isinstance(schema, dict)
            assert "properties" in schema
            assert "timeline" in schema["properties"]
            assert "type" in schema
            assert schema["type"] == "object"
            
        except SchemaToolsError as e:
            # If schema file doesn't exist, skip this test
            pytest.skip(f"Scene DSL schema not found: {e}")
    
    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_load_nonexistent_schema_raises_error(self, mock_file):
        """Test that missing schema file raises SchemaToolsError."""
        with pytest.raises(SchemaToolsError, match="Scene DSL schema not found"):
            load_scene_dsl_schema()
    
    @patch("builtins.open", mock_open(read_data='{"invalid": json}'))
    def test_load_invalid_json_raises_error(self):
        """Test that invalid JSON in schema raises SchemaToolsError."""
        with pytest.raises(SchemaToolsError, match="Invalid JSON in Scene DSL schema"):
            load_scene_dsl_schema()


class TestConvertToOpenaiSchema:
    """Test cases for converting schema to OpenAI format."""
    
    def test_convert_simple_schema(self):
        """Test converting a simple schema."""
        input_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"}
            }
        }
        
        result = convert_to_openai_schema(input_schema)
        
        assert result["type"] == "object"
        assert result["additionalProperties"] is False
        assert "properties" in result
        assert "name" in result["properties"]
        assert "age" in result["properties"]
    
    def test_convert_nested_schema(self):
        """Test converting schema with nested objects."""
        input_schema = {
            "type": "object",
            "properties": {
                "person": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "details": {
                            "type": "object", 
                            "properties": {
                                "age": {"type": "number"}
                            }
                        }
                    }
                }
            }
        }
        
        result = convert_to_openai_schema(input_schema)
        
        # Check that additionalProperties is set at all levels
        assert result["additionalProperties"] is False
        assert result["properties"]["person"]["additionalProperties"] is False
        assert result["properties"]["person"]["properties"]["details"]["additionalProperties"] is False
    
    def test_convert_array_schema(self):
        """Test converting schema with arrays."""
        input_schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "value": {"type": "string"}
                        }
                    }
                }
            }
        }
        
        result = convert_to_openai_schema(input_schema)
        
        # Check array item schema is processed
        item_schema = result["properties"]["items"]["items"]
        assert item_schema["additionalProperties"] is False
        assert "properties" in item_schema


class TestCreateOpenaiFormatSpec:
    """Test cases for creating OpenAI format specification."""
    
    @patch('agents.schema_tools.load_scene_dsl_schema')
    def test_create_format_spec_success(self, mock_load_schema):
        """Test successful creation of format spec."""
        mock_schema = {
            "type": "object",
            "properties": {
                "scene_id": {"type": "string"},
                "timeline": {"type": "array", "items": {"type": "object"}}
            }
        }
        mock_load_schema.return_value = mock_schema
        
        format_spec = create_openai_format_spec("test_schema")
        
        assert format_spec["type"] == "json_schema"
        assert format_spec["json_schema"]["name"] == "test_schema"
        assert format_spec["json_schema"]["strict"] is True
        assert "schema" in format_spec["json_schema"]
        
        schema = format_spec["json_schema"]["schema"]
        assert schema["type"] == "object"
        assert "properties" in schema
    
    @patch('agents.schema_tools.load_scene_dsl_schema')
    def test_create_format_spec_with_schema_error(self, mock_load_schema):
        """Test format spec creation with schema loading error."""
        mock_load_schema.side_effect = SchemaToolsError("Schema load failed")
        
        with pytest.raises(SchemaToolsError, match="Failed to create OpenAI format spec"):
            create_openai_format_spec()


class TestValidateOpenaiCompatibility:
    """Test cases for OpenAI compatibility validation."""
    
    def test_compatible_schema(self):
        """Test validation of compatible schema."""
        compatible_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "nested": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "value": {"type": "number"}
                    }
                }
            },
            "additionalProperties": False
        }
        
        issues = validate_openai_compatibility(compatible_schema)
        assert len(issues) == 0
    
    def test_incompatible_schema_unsupported_keywords(self):
        """Test validation of schema with unsupported keywords."""
        incompatible_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            },
            "patternProperties": {
                "^S_": {"type": "string"}
            },
            "if": {
                "properties": {"name": {"const": "test"}}
            },
            "then": {
                "required": ["name"]
            }
        }
        
        issues = validate_openai_compatibility(incompatible_schema)
        
        # Should have issues for unsupported keywords
        assert len(issues) > 0
        assert any("patternProperties" in issue for issue in issues)
        assert any("if" in issue for issue in issues)
        assert any("then" in issue for issue in issues)
    
    def test_missing_additional_properties(self):
        """Test validation of schema missing additionalProperties."""
        schema_missing_props = {
            "type": "object",
            "properties": {
                "nested": {
                    "type": "object",  # Missing additionalProperties
                    "properties": {
                        "value": {"type": "string"}
                    }
                }
            }
        }
        
        issues = validate_openai_compatibility(schema_missing_props)
        
        # Should have issues for missing additionalProperties
        assert len(issues) > 0
        assert any("additionalProperties" in issue for issue in issues)


class TestGetOperationSchemas:
    """Test cases for extracting operation schemas."""
    
    @patch('agents.schema_tools.load_scene_dsl_schema')
    def test_get_operation_schemas_success(self, mock_load_schema):
        """Test successful extraction of operation schemas."""
        mock_schema = {
            "properties": {
                "timeline": {
                    "items": {
                        "oneOf": [
                            {
                                "properties": {
                                    "op": {"enum": ["title"]},
                                    "text": {"type": "string"}
                                }
                            },
                            {
                                "properties": {
                                    "op": {"enum": ["text"]},
                                    "text": {"type": "string"},
                                    "pos": {"type": "string"}
                                }
                            }
                        ]
                    }
                }
            }
        }
        mock_load_schema.return_value = mock_schema
        
        operations = get_operation_schemas()
        
        assert isinstance(operations, dict)
        assert "title" in operations
        assert "text" in operations
        assert len(operations) == 2
    
    @patch('agents.schema_tools.load_scene_dsl_schema')
    def test_get_operation_schemas_missing_oneof(self, mock_load_schema):
        """Test operation extraction with missing oneOf."""
        mock_schema = {
            "properties": {
                "timeline": {
                    "items": {
                        # Missing oneOf
                        "properties": {
                            "op": {"enum": ["title"]}
                        }
                    }
                }
            }
        }
        mock_load_schema.return_value = mock_schema
        
        with pytest.raises(SchemaToolsError, match="Scene DSL schema missing oneOf"):
            get_operation_schemas()


class TestCreateOperationExamples:
    """Test cases for creating operation examples."""
    
    def test_create_operation_examples(self):
        """Test creation of operation examples."""
        examples = create_operation_examples()
        
        assert isinstance(examples, dict)
        assert len(examples) > 0
        
        # Check for key operations
        expected_ops = ["title", "subtitle", "text", "eq", "graph2d", "pause", "clear"]
        for op in expected_ops:
            assert op in examples
            
            # Check example structure
            example = examples[op]
            assert isinstance(example, dict)
            assert "op" in example
            assert example["op"] == op
    
    def test_operation_examples_valid_structure(self):
        """Test that operation examples have valid structure."""
        examples = create_operation_examples()
        
        for op_name, example in examples.items():
            assert example["op"] == op_name
            
            # Check common fields based on operation type
            if op_name in ["title", "subtitle", "text"]:
                assert "text" in example
                assert "pos" in example
                assert "anim" in example
            elif op_name == "eq":
                assert "latex" in example
                assert "pos" in example
                assert "anim" in example
            elif op_name == "graph2d":
                assert "fn" in example
                assert "x_min" in example
                assert "x_max" in example
                assert "y_min" in example
                assert "y_max" in example
            elif op_name == "pause":
                assert "seconds" in example
                assert isinstance(example["seconds"], (int, float))
            elif op_name == "clear":
                assert "anim" in example


class TestSchemaToolsIntegration:
    """Integration tests for schema tools."""
    
    def test_full_pipeline_with_mock_schema(self):
        """Test the complete pipeline from schema loading to format spec creation."""
        mock_schema = {
            "type": "object",
            "properties": {
                "scene_id": {
                    "type": "string",
                    "pattern": "^[a-z0-9_]+$"
                },
                "timeline": {
                    "type": "array",
                    "items": {
                        "oneOf": [
                            {
                                "properties": {
                                    "op": {"enum": ["title"]},
                                    "text": {"type": "string", "maxLength": 160},
                                    "pos": {"enum": ["top", "center", "bottom"]},
                                    "anim": {"enum": ["write", "fade"]}
                                },
                                "required": ["op", "text"],
                                "additionalProperties": False
                            }
                        ]
                    }
                }
            },
            "required": ["scene_id", "timeline"]
        }
        
        with patch.object(schema_tools, 'load_scene_dsl_schema', return_value=mock_schema) as mock_load:
            # Test schema loading
            loaded_schema = schema_tools.load_scene_dsl_schema()
            assert loaded_schema == mock_schema
            mock_load.assert_called_once()
            
            # Test OpenAI conversion
            openai_schema = schema_tools.convert_to_openai_schema(loaded_schema)
            assert openai_schema["additionalProperties"] is False
            
            # Test compatibility validation
            issues = schema_tools.validate_openai_compatibility(openai_schema)
            assert len(issues) == 0  # Should be compatible
            
            # Test format spec creation
            format_spec = schema_tools.create_openai_format_spec("test")
            assert format_spec["json_schema"]["strict"] is True
            
            # Test operation extraction
            operations = schema_tools.get_operation_schemas()
            assert "title" in operations


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
