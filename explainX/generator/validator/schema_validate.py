"""
Schema validation module for Scene DSL.

This module provides validation functionality for Scene DSL JSON documents
against the defined JSON schema. It ensures that all scenes conform to the
expected structure and constraints before processing.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import jsonschema
from jsonschema import Draft7Validator, ValidationError


class SceneValidationError(Exception):
    """Custom exception for scene validation errors."""

    def __init__(self, message: str, field_path: str = None, value: Any = None):
        self.field_path = field_path
        self.value = value
        super().__init__(message)


class SceneValidator:
    """Validates Scene DSL documents against the JSON schema."""

    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize the validator with the schema.

        Args:
            schema_path: Path to the JSON schema file. If None, uses default location.
        """
        if schema_path is None:
            # Default to schema in compiler directory
            current_dir = Path(__file__).parent
            schema_path = current_dir.parent / "compiler" / "schema.json"

        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()
        self.validator = Draft7Validator(self.schema)

    def _load_schema(self) -> Dict[str, Any]:
        """Load and return the JSON schema."""
        try:
            with open(self.schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)
            return schema
        except FileNotFoundError:
            raise SceneValidationError(f"Schema file not found: {self.schema_path}")
        except json.JSONDecodeError as e:
            raise SceneValidationError(f"Invalid JSON in schema file: {e}")

    def validate_scene(self, scene_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a single scene against the schema.

        Args:
            scene_data: Scene data dictionary to validate

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        try:
            self.validator.validate(scene_data)
            return True, []
        except ValidationError as e:
            error_messages = self._format_validation_errors([e])
            return False, error_messages

    def validate_scenes(
        self, scenes: List[Dict[str, Any]]
    ) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Validate multiple scenes.

        Args:
            scenes: List of scene data dictionaries

        Returns:
            Tuple of (all_valid, dict mapping scene_id to error messages)
        """
        all_valid = True
        scene_errors = {}

        for scene in scenes:
            scene_id = scene.get("scene_id", "unknown")
            is_valid, errors = self.validate_scene(scene)

            if not is_valid:
                all_valid = False
                scene_errors[scene_id] = errors

        return all_valid, scene_errors

    def validate_full_plan(self, plan_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a complete video plan including all scenes.

        Args:
            plan_data: Full plan data with video_id, title, scenes, etc.

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors = []

        # Validate required top-level fields
        required_fields = ["video_id", "title", "scenes"]
        for field in required_fields:
            if field not in plan_data:
                errors.append(f"Missing required field: {field}")

        if errors:
            return False, errors

        # Validate scenes
        scenes = plan_data.get("scenes", [])
        if not scenes:
            errors.append("No scenes provided")
            return False, errors

        scenes_valid, scene_errors = self.validate_scenes(scenes)

        # Flatten scene errors into main error list
        for scene_id, scene_error_list in scene_errors.items():
            for error in scene_error_list:
                errors.append(f"Scene '{scene_id}': {error}")

        return scenes_valid, errors

    def _format_validation_errors(
        self, validation_errors: List[ValidationError]
    ) -> List[str]:
        """
        Format JSON schema validation errors into readable messages.

        Args:
            validation_errors: List of ValidationError objects

        Returns:
            List of formatted error message strings
        """
        formatted_errors = []

        for error in validation_errors:
            field_path = (
                ".".join(str(p) for p in error.absolute_path)
                if error.absolute_path
                else "root"
            )

            # Create a more user-friendly error message
            if error.validator == "required":
                missing_field = (
                    error.message.split("'")[1] if "'" in error.message else "unknown"
                )
                formatted_errors.append(
                    f"Missing required field '{missing_field}' in {field_path}"
                )
            elif error.validator == "enum":
                formatted_errors.append(
                    f"Invalid value at {field_path}: {error.message}"
                )
            elif error.validator == "maxLength":
                formatted_errors.append(
                    f"Value too long at {field_path}: {error.message}"
                )
            elif error.validator == "pattern":
                formatted_errors.append(
                    f"Invalid format at {field_path}: {error.message}"
                )
            elif error.validator == "type":
                formatted_errors.append(
                    f"Wrong data type at {field_path}: {error.message}"
                )
            else:
                formatted_errors.append(
                    f"Validation error at {field_path}: {error.message}"
                )

        return formatted_errors

    def get_supported_operations(self) -> List[str]:
        """Return list of supported operations from the schema."""
        timeline_items = self.schema["properties"]["timeline"]["items"]
        op_enum = timeline_items["properties"]["op"]["enum"]
        return op_enum

    def get_schema_version(self) -> str:
        """Return the schema version/ID."""
        return self.schema.get("$id", "unknown")


# Convenience functions for direct usage
def validate_scene_dict(scene_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Convenience function to validate a single scene dictionary.

    Args:
        scene_data: Scene data dictionary

    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    validator = SceneValidator()
    return validator.validate_scene(scene_data)


def validate_plan_dict(plan_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Convenience function to validate a complete plan dictionary.

    Args:
        plan_data: Complete plan data dictionary

    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    validator = SceneValidator()
    return validator.validate_full_plan(plan_data)
