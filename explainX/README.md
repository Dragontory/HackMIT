# ExplainX Video Generation System

A comprehensive system for converting student PDF notes into educational videos using Manim animations.

## Overview

This system transforms structured Scene Plans into deterministic, safe, and attractive Manim educational videos. It supports both 2D and 3D visuals with automatic selection and manual overrides, designed to run fast at scale through parallel processing.

## Project Structure

```
generator/
├── compiler/           # Scene DSL compiler
│   ├── schema.json    # Complete JSON Schema for Scene DSL
│   └── __init__.py
├── validator/         # Validation pipeline
│   ├── schema_validate.py  # Schema validation implementation
│   └── __init__.py
├── tests/            # Comprehensive test suite
│   ├── test_schema_validation.py  # Schema validation tests
│   └── __init__.py
├── assets_cache/     # Content-addressed asset storage
└── tmp_builds/       # Temporary build artifacts
```

## Ticket 1 Implementation ✅

**Completed**: JSON Schema for Scene DSL

### Features Implemented:

#### 1. Comprehensive JSON Schema (`generator/compiler/schema.json`)

- **All 17 operations supported**: title, subtitle, bullet, eq, image, callout, highlight, pause, transform_eq, graph2d, axes2d, surface3d, vector3d, camera_move, table, box, arrow
- **Strict validation constraints**:
  - Text fields limited to 160 characters
  - LaTeX expressions limited to 480 characters
  - Asset references must use sha256 content-addressing
  - Function expressions use safe subset only
  - Camera parameters within valid ranges
- **Operation-specific requirements**: Each operation validates its required fields (e.g., `eq` requires `latex`, `pause` requires `seconds`)

#### 2. Robust Schema Validator (`generator/validator/schema_validate.py`)

- **SceneValidator class** with comprehensive validation logic
- **Detailed error reporting** with field paths and user-friendly messages
- **Support for single scenes and full video plans**
- **Convenience functions** for easy integration
- **Asset reference validation** with proper content-addressing

#### 3. Comprehensive Test Suite (`generator/tests/test_schema_validation.py`)

- **25 test cases** covering all validation scenarios
- **Positive tests**: Valid scenes with mixed operations pass
- **Negative tests**:
  - Unknown operations are rejected ✅
  - Overlong LaTeX is rejected ✅
  - Invalid patterns are caught ✅
  - Missing required fields are detected ✅
- **Real-world examples**: Gradient descent tutorial validation ✅

### Validation Results

All tests pass successfully with clear, actionable error messages:

```bash
$ python -m pytest generator/tests/test_schema_validation.py -v
============================================ 25 passed in 0.12s ============================================
```

### Key Technical Achievements

1. **Schema Design**: Complete JSON Schema with operation-specific conditional validation using `allOf` and `if/then` constructs
2. **Error Handling**: User-friendly error messages that specify exact field paths and validation issues
3. **Safety**: Mathematical function expressions are restricted to safe subset preventing code injection
4. **Extensibility**: Modular design supports easy addition of new operations
5. **Performance**: Fast validation suitable for high-throughput processing

## Example Usage

```python
from generator.validator import validate_scene_dict, validate_plan_dict

# Validate a single scene
scene = {
    "scene_id": "intro_01",
    "timeline": [
        {"op": "title", "text": "Linear Algebra Basics", "pos": "top"},
        {"op": "eq", "latex": "Ax = b", "anim": "write"},
        {"op": "pause", "seconds": 1.2}
    ]
}

is_valid, errors = validate_scene_dict(scene)
# Returns: (True, [])
```

## Ticket 2 Implementation ✅

**Completed**: Style Pack Loader & Validator

### Features Implemented:

#### 1. Comprehensive JSON Schema (`generator/style/schema/style_schema.json`)

- **Complete style pack specification** with typography, colors, layout, graph defaults, camera settings, and animations
- **Strict validation** including color hex patterns, scale ranges, font fallbacks, and margin constraints
- **Flexible defaults** allowing minimal style packs to work with sensible defaults
- **Type safety** with proper validation of all numeric ranges and enum values

#### 2. Domain Models (`generator/style/models.py`)

- **Immutable dataclasses** with built-in validation and type safety
- **Enums** for structured values like TitlePosition
- **Nested validation** ensuring all values are within acceptable ranges
- **Clean separation** between data structure and business logic

#### 3. Normalization System (`generator/style/normalize.py`)

- **Color normalization** converting hex colors to consistent uppercase format
- **Font list validation** with fallback support and length constraints
- **Numeric validation** for scales, margins, angles, and other measurements
- **Error reporting** with precise field paths for debugging

#### 4. Style Loader (`generator/style/loader.py`)

- **Multi-source loading** from dictionaries, files, or Path objects
- **Schema validation** with clear error messages and field paths
- **Default application** automatically filling missing values
- **Style merging** for creating theme variations and overrides
- **Normalization integration** ensuring all values are properly formatted

#### 5. StyleProvider Interface (`generator/style/provider.py`)

- **Clean abstraction** for compiler consumption without domain model coupling
- **Read-only access** preventing accidental style modifications
- **Convenient methods** for accessing common styling properties
- **Future-proof design** allowing implementation changes without breaking compiler

#### 6. Sample Style Packs

- **Educational default** (`edu_default_v1.json`) with clean, professional styling
- **Dark high contrast** (`dark_high_contrast.json`) for accessibility and modern appearance
- **Real-world examples** demonstrating complete style pack capabilities

### Test Coverage: 43 Tests ✅

- **Normalization tests**: 18 tests covering color, font, numeric, and range validation
- **Loader tests**: 14 tests covering validation, loading, merging, and file operations
- **Merging tests**: 11 tests covering simple and complex style combination scenarios
- **Integration tests** with real sample files and error handling
- **Table-driven tests** for comprehensive edge case coverage

### Key Technical Achievements

1. **Schema-First Design**: Complete JSON Schema enables IDE support and external validation
2. **Immutable Architecture**: Frozen dataclasses prevent accidental style modifications
3. **Comprehensive Validation**: Multi-layer validation (schema, normalization, domain model)
4. **Style Inheritance**: Sophisticated merging allows theme customization and brand variants
5. **Type Safety**: Full type hints and runtime validation ensure reliability
6. **Clean Architecture**: Provider interface decouples compiler from implementation details

### Example Usage

```python
from generator.style import load_style_pack, create_style_provider

# Load and merge styles
base_style = load_style_pack("edu_default_v1.json")
custom_colors = {"colors": {"accent": "#FF6B35", "highlight": "#FFF3CD"}}
merged_style = loader.merge_styles(base_style, custom_colors)

# Use in compiler via clean interface
provider = create_style_provider(merged_style)
title_color = provider.get_primary_text_color()  # "#111111"
title_scale = provider.get_title_scale()         # 0.9
```

## Next Steps

The style and validation foundations are complete. Ready for:

- **Ticket 3**: Scene Compiler Implementation
- **Ticket 4**: 2D/3D Operation Handlers
- **Ticket 5**: Manim Code Generation
- **Ticket 6**: Validation Pipeline with Sandboxing

## System Status

### ✅ Completed Components

- **Scene DSL Validation**: 25 tests passing - Complete schema validation for all 17 operations
- **Style Pack System**: 54 tests passing - Full style loading, validation, normalization, merging, and pre-Manim adapters
- **Codegen Agent System**: 49 tests passing - GPT-5 powered Scene DSL generation with enterprise infrastructure

## Ticket 2.4 Implementation ✅

**Completed**: Pre-Manim Adapter Functions

### Features Added:

#### 1. Color Conversion (`normalize.py`)

- **`color_tuple(rgb_hex: str) -> tuple[int, int, int]`** - Converts hex colors to RGB tuples (0-255 range)
- **Perfect accuracy** - `color_tuple("#2563EB")` returns `(37, 99, 235)` as specified
- **Comprehensive validation** - Handles invalid formats with clear error messages
- **Case insensitive** - Accepts both `#ff0000` and `#FF0000`

#### 2. StyleProvider Convenience Methods (`provider.py`)

- **`get_title_position_enum() -> str`** - Returns position as string literal (`"top"`, `"center"`, `"bottom"`)
- **`get_text_scales() -> dict[str, float]`** - Returns scales as `{"title": 1.1, "subtitle": 0.8, "text": 0.85, "eq": 1.05}`
- **Compiler-friendly formats** - Easy to use in conditional logic and calculations
- **Type-safe returns** - All values properly typed for static analysis

#### 3. No Manim Dependencies

- **Zero Manim imports** - All functions work independently
- **Unit testable** - Can test color handling without graphics dependencies
- **Clean separation** - Compiler decides how to adapt values to Manim calls

### Test Coverage: 11 New Tests ✅

- **Color conversion tests** - Basic conversions, edge cases, invalid formats
- **Provider adapter tests** - Position enums, scale dictionaries, defaults
- **Integration tests** - No Manim imports, compiler-friendly formats
- **Specification compliance** - All examples from ticket requirements verified

### Example Usage for Compiler

```python
from generator.style import color_tuple, load_style_pack, create_style_provider

# Load style and create provider
style = load_style_pack("edu_default_v1.json")
provider = create_style_provider(style)

# Get RGB tuple for graphics libraries
accent_rgb = color_tuple(provider.get_accent_color())  # (37, 99, 235)

# Get type-safe scales for text sizing
scales = provider.get_text_scales()  # {"title": 0.9, "subtitle": 0.7, ...}
title_size = base_size * scales["title"]

# Get position for conditional logic
if provider.get_title_position_enum() == "center":
    # Center the title on screen
```

## Ticket 3 Implementation ✅

**Completed**: OpenAI Codegen Agent System

### Features Added:

#### 1. GPT-5 Client with Structured Outputs (`client_openai.py`)

- **OpenAI Structured Outputs** - Constrains GPT-5 output to Scene DSL schema
- **Adaptive Rate Limiting** - Token bucket with 429 response handling
- **Retry Logic** - Exponential backoff with timeout handling
- **Mock Client** - Full-featured mock for development without API calls
- **Token Usage Tracking** - Comprehensive metrics and cost monitoring

#### 2. Schema Integration (`schema_tools.py`)

- **Schema Binding** - Converts Scene DSL schema to OpenAI format
- **Compatibility Validation** - Ensures schema works with structured outputs
- **Operation Examples** - Sample JSON for each Scene DSL operation
- **Schema Loading** - Automatic loading from Ticket 1 schema files

#### 3. Advanced Prompt Engineering (`prompts.py`)

- **Style-Aware Prompts** - Uses StyleProvider from Ticket 2 for consistency
- **Adaptive Content Detection** - Automatically detects math/science/example content
- **Context-Rich Templates** - Educational prompt patterns optimized for learning
- **Repair Prompts** - Specialized prompts for fixing validation errors

#### 4. Enterprise-Grade Infrastructure

- **Content-Addressed Caching** (`cache.py`) - SHA-256 based with TTL and LRU eviction
- **Rate Limiting** (`rate_limit.py`) - Token bucket + adaptive adjustment
- **Data Transfer Objects** (`dto.py`) - Type-safe immutable contracts
- **Batch Processing** - Concurrent generation with error isolation
- **Repair Service** (`repair_service.py`) - Automatically fixes invalid JSON

#### 5. Production-Ready Service (`codegen_service.py`)

- **Sync & Async Generation** - Full asyncio support with concurrent batching
- **Input Validation** - Comprehensive constraint checking
- **Error Handling** - Graceful degradation with structured error responses
- **Observability** - Service status, metrics, and health checks
- **Integration Ready** - Clean interfaces for compiler consumption

### Test Coverage: 49 New Tests ✅

- **DTO Tests**: Data contract validation and error handling
- **Schema Tools Tests**: OpenAI integration and compatibility validation
- **Integration Tests**: End-to-end generation with caching and batch processing
- **Mock Testing**: Complete functionality without external dependencies
- **Error Scenarios**: Comprehensive failure mode validation

### Example Usage

```python
from generator.agents import CodegenService, CodegenInput
from generator.style import load_style_pack

# Initialize service
service = CodegenService(openai_api_key="sk-...")  # or use_mock_client=True

# Create input
input_data = CodegenInput(
    video_id="physics_101",
    scene_id="intro_forces",
    section_heading="Newton's Laws of Motion",
    section_text="Force equals mass times acceleration: F = ma...",
    style=load_style_pack("physics_style.json"),
    constraints={"max_operations": 15, "prefer_2d": True}
)

# Generate Scene DSL JSON
output = service.generate_scene_sync(input_data)
scene_json = output.scene_json  # Ready for Manim compiler!
```

### 🎯 Total Test Coverage: 128 Tests Passing

**System Status**: Production-ready foundation with enterprise-grade reliability!

- **Scene DSL Validation**: 25 tests - Complete schema validation
- **Style Pack System**: 54 tests - Full styling with pre-Manim adapters
- **Codegen Agent System**: 49 tests - GPT-5 integration with comprehensive infrastructure

The complete pipeline is now ready: **Processor → Codegen Agents → Scene DSL → Compiler**

## Requirements

- Python 3.10+
- jsonschema >= 4.17.0
- OpenAI API key (for production use)

### Environment Setup

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure OpenAI API Key (choose one method):**

   **Option A: .env file (recommended for development)**

   ```bash
   # Create .env file in project root
   echo "OPENAI_API_KEY=sk-your-actual-api-key-here" > .env
   ```

   **Option B: Environment variable**

   ```bash
   export OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

   **Option C: Pass directly in code**

   ```python
   service = CodegenService(openai_api_key="sk-your-actual-api-key-here")
   ```

3. **For development/testing without API costs:**
   ```python
   # Use mock client (no API key needed)
   service = CodegenService(use_mock_client=True)
   ```

- pytest >= 7.2.0 (for testing)
- manim >= 0.17.0 (for future compilation steps)
