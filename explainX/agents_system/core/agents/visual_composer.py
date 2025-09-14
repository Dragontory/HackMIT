"""
Visual Composer Agent implementation.

This agent composes and coordinates visual elements in Manim animations,
optimizing layout, timing, and visual coherence.
"""

import logging
import re
import time
import uuid
from typing import List, Dict, Any, Tuple, Optional, Set

from ...domain.interfaces import IAgent
from ...domain.models import (
    AgentState,
    AgentResult,
    VisualCompositionResult,
    VisualComposition,
    VisualElement,
)
from ...infrastructure.anthropic.client import AnthropicClient
from ...infrastructure.anthropic.models import ClaudeMessage


logger = logging.getLogger(__name__)


class VisualComposerAgent(IAgent):
    """
    Specialized agent for composing and coordinating visual elements in Manim animations.

    Uses Claude's visual design understanding to:
    - Analyze existing visual elements and their relationships
    - Optimize layout and positioning for clarity and aesthetics
    - Coordinate animations and transitions for coherent flow
    - Balance visual complexity with educational clarity
    - Ensure consistent visual style and theming
    """

    def __init__(self, claude_client: AnthropicClient):
        self.claude_client = claude_client
        self._system_prompt = self._create_system_prompt()

    @property
    def name(self) -> str:
        return "VisualComposerAgent"

    @property
    def description(self) -> str:
        return "Composes and coordinates visual elements"

    async def process(self, state: AgentState) -> AgentResult:
        """Process state and compose visual elements."""
        start_time = time.time()

        try:
            logger.info(f"Visual Composer processing: {state['content_title']}")

            # Get the code to analyze and enhance
            manim_code = state.get("manim_code", "")

            if not manim_code:
                # Create sample code for testing
                manim_code = self._create_sample_manim_code()
                logger.info("No Manim code provided, using sample code")

            # Perform visual composition
            result = await self.compose_visuals(manim_code)

            # Update state
            state["visual_composition_result"] = result
            state["manim_code"] = result.enhanced_code
            state["current_agent"] = self.name
            state["processing_stage"] = "visual_composition_complete"

            processing_time = time.time() - start_time
            result.processing_time = processing_time

            return AgentResult(
                success=result.success,
                data=result,
                metadata={
                    "agent": self.name,
                    "compositions_created": len(result.compositions),
                    "elements_composed": sum(
                        len(comp.elements) for comp in result.compositions
                    ),
                    "suggestions_made": len(result.element_suggestions)
                    + len(result.layout_improvements)
                    + len(result.animation_improvements),
                    "processing_time": processing_time,
                },
            )

        except Exception as e:
            logger.error(f"Visual Composer error: {e}")
            return AgentResult(
                success=False,
                data=None,
                errors=[f"Visual composition failed: {str(e)}"],
            )

    async def compose_visuals(self, manim_code: str) -> VisualCompositionResult:
        """
        Compose visual elements in Manim code.

        Args:
            manim_code: The Manim Python code to analyze and enhance

        Returns:
            VisualCompositionResult: Complete results with compositions and suggestions
        """

        # Step 1: Analyze existing visual elements
        compositions = await self.analyze_visual_elements(manim_code)

        # Step 2: Generate layout improvements
        layout_improvements = await self.generate_layout_improvements(
            manim_code, compositions
        )

        # Step 3: Generate animation improvements
        animation_improvements = await self.generate_animation_improvements(
            manim_code, compositions
        )

        # Step 4: Generate new element suggestions
        element_suggestions = await self.generate_element_suggestions(
            manim_code, compositions
        )

        # Step 5: Apply improvements to code
        enhanced_code = await self.apply_improvements(
            manim_code, layout_improvements, animation_improvements
        )

        # Determine success
        success = len(compositions) > 0 and enhanced_code != manim_code

        return VisualCompositionResult(
            original_code=manim_code,
            enhanced_code=enhanced_code,
            compositions=compositions,
            element_suggestions=element_suggestions,
            layout_improvements=layout_improvements,
            animation_improvements=animation_improvements,
            success=success,
        )

    async def analyze_visual_elements(self, code: str) -> List[VisualComposition]:
        """Analyze and extract visual elements from Manim code."""

        # Prepare context for Claude
        context_parts = ["I need to analyze the visual elements in this Manim code:"]
        context_parts.append(f"```python\n{code}\n```")

        context_parts.append(
            "Please identify all visual elements (mobjects), their properties, positions, animations, and how they relate to each other. "
            "Organize them into coherent compositions based on scenes or logical groupings."
        )

        messages = [
            ClaudeMessage(
                role="user",
                content="\n\n".join(context_parts),
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)

        # Parse the response to extract compositions
        return self._parse_visual_compositions(response.content, code)

    async def generate_layout_improvements(
        self, code: str, compositions: List[VisualComposition]
    ) -> List[Dict[str, Any]]:
        """Generate layout improvements for visual elements."""

        if not compositions:
            return []

        # Prepare context for Claude
        context_parts = [
            "I need to improve the layout of visual elements in this Manim code:"
        ]
        context_parts.append(f"```python\n{code}\n```")

        # Add information about existing compositions
        context_parts.append("I've identified these visual compositions:")
        for comp in compositions:
            context_parts.append(f"- {comp.title}: {len(comp.elements)} elements")

        context_parts.append(
            "Please suggest specific layout improvements to enhance clarity, balance, and visual appeal. "
            "Focus on positioning, alignment, grouping, and spacing of elements."
        )

        messages = [
            ClaudeMessage(
                role="user",
                content="\n\n".join(context_parts),
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)

        # Parse the response to extract layout improvements
        return self._parse_layout_improvements(response.content)

    async def generate_animation_improvements(
        self, code: str, compositions: List[VisualComposition]
    ) -> List[Dict[str, Any]]:
        """Generate animation improvements for visual elements."""

        if not compositions:
            return []

        # Prepare context for Claude
        context_parts = ["I need to improve the animations in this Manim code:"]
        context_parts.append(f"```python\n{code}\n```")

        # Add information about existing compositions
        context_parts.append("I've identified these visual compositions:")
        for comp in compositions:
            context_parts.append(
                f"- {comp.title}: {len(comp.elements)} elements with {len(comp.timeline)} animation steps"
            )

        context_parts.append(
            "Please suggest specific animation improvements to enhance flow, timing, and visual coherence. "
            "Focus on animation types, durations, sequencing, and transitions between elements."
        )

        messages = [
            ClaudeMessage(
                role="user",
                content="\n\n".join(context_parts),
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)

        # Parse the response to extract animation improvements
        return self._parse_animation_improvements(response.content)

    async def generate_element_suggestions(
        self, code: str, compositions: List[VisualComposition]
    ) -> List[Dict[str, Any]]:
        """Generate suggestions for new visual elements."""

        # Prepare context for Claude
        context_parts = [
            "I need suggestions for additional visual elements to enhance this Manim code:"
        ]
        context_parts.append(f"```python\n{code}\n```")

        # Add information about existing compositions
        if compositions:
            context_parts.append("I've identified these existing visual compositions:")
            for comp in compositions:
                context_parts.append(f"- {comp.title}: {len(comp.elements)} elements")

        context_parts.append(
            "Please suggest specific new visual elements that would enhance the educational value and visual appeal. "
            "Focus on elements that would clarify concepts, highlight key points, or improve engagement."
        )

        messages = [
            ClaudeMessage(
                role="user",
                content="\n\n".join(context_parts),
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)

        # Parse the response to extract element suggestions
        return self._parse_element_suggestions(response.content)

    async def apply_improvements(
        self,
        code: str,
        layout_improvements: List[Dict[str, Any]],
        animation_improvements: List[Dict[str, Any]],
    ) -> str:
        """Apply improvements to the Manim code."""

        if not layout_improvements and not animation_improvements:
            return code

        # Prepare context for Claude
        context_parts = ["I need to apply these improvements to this Manim code:"]
        context_parts.append(f"```python\n{code}\n```")

        # Add layout improvements
        if layout_improvements:
            context_parts.append("Layout improvements to apply:")
            for i, improvement in enumerate(layout_improvements, 1):
                context_parts.append(f"{i}. {improvement['description']}")
                if "code_change" in improvement:
                    context_parts.append(f"   Code: {improvement['code_change']}")

        # Add animation improvements
        if animation_improvements:
            context_parts.append("Animation improvements to apply:")
            for i, improvement in enumerate(animation_improvements, 1):
                context_parts.append(f"{i}. {improvement['description']}")
                if "code_change" in improvement:
                    context_parts.append(f"   Code: {improvement['code_change']}")

        context_parts.append(
            "Please apply these improvements to the code and provide the complete enhanced version. "
            "Make sure the code remains functional and follows Manim best practices."
        )

        messages = [
            ClaudeMessage(
                role="user",
                content="\n\n".join(context_parts),
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)

        # Extract the enhanced code from the response
        return self._extract_enhanced_code(response.content, code)

    def _parse_visual_compositions(
        self, response: str, code: str
    ) -> List[VisualComposition]:
        """Parse visual compositions from Claude's response."""

        compositions = []

        # Look for composition blocks
        composition_blocks = re.findall(
            r"(?:Composition|Scene|Visual Group|Visual Composition)[^\n]*?:(.*?)(?=(?:Composition|Scene|Visual Group|Visual Composition)|$)",
            response,
            re.DOTALL,
        )

        if not composition_blocks:
            # Try to find a more general structure
            composition_blocks = [response]

        for i, block in enumerate(composition_blocks):
            composition_id = f"composition_{uuid.uuid4().hex[:8]}"
            title = f"Composition {i+1}"

            # Try to extract a title
            title_match = re.search(
                r"(?:Composition|Scene|Visual Group)[^\n]*?:\s*(.*?)(?:\n|$)", block
            )
            if title_match:
                title = title_match.group(1).strip()

            # Extract elements
            elements = []
            element_blocks = re.findall(
                r"(?:Element|Mobject|Object)[^\n]*?:(.*?)(?=(?:Element|Mobject|Object)|$)",
                block,
                re.DOTALL,
            )

            if not element_blocks:
                # Try to find elements with bullet points
                element_blocks = re.findall(
                    r"[-*]\s+(.*?)(?=[-*]|\n\n|$)", block, re.DOTALL
                )

            for j, element_block in enumerate(element_blocks):
                element_id = f"element_{uuid.uuid4().hex[:8]}"
                element_type = "unknown"
                content = ""

                # Try to determine element type
                if "Text" in element_block or "text" in element_block:
                    element_type = "text"
                elif (
                    "MathTex" in element_block
                    or "math" in element_block
                    or "equation" in element_block
                ):
                    element_type = "equation"
                elif (
                    "Rectangle" in element_block
                    or "Circle" in element_block
                    or "Arrow" in element_block
                ):
                    element_type = "shape"
                elif (
                    "Graph" in element_block
                    or "Axes" in element_block
                    or "plot" in element_block
                ):
                    element_type = "graph"
                elif "Image" in element_block or "SVG" in element_block:
                    element_type = "image"

                # Extract content
                content_match = re.search(
                    r"content:?\s*[\"']?(.*?)[\"']?(?:\n|$)",
                    element_block,
                    re.IGNORECASE,
                )
                if content_match:
                    content = content_match.group(1).strip()
                else:
                    # Try to extract from code
                    code_match = re.search(
                        r"[A-Za-z_]+\s*\(\s*[\"'](.*?)[\"']", element_block
                    )
                    if code_match:
                        content = code_match.group(1).strip()

                # Extract position
                position = None
                position_match = re.search(
                    r"position:?\s*(.*?)(?:\n|$)", element_block, re.IGNORECASE
                )
                if position_match:
                    pos_str = position_match.group(1).strip()
                    # Try to parse x, y, z coordinates
                    coord_match = re.search(
                        r"x:?\s*([-\d.]+).*?y:?\s*([-\d.]+)", pos_str, re.IGNORECASE
                    )
                    if coord_match:
                        position = {
                            "x": float(coord_match.group(1)),
                            "y": float(coord_match.group(2)),
                        }
                    else:
                        # Try to parse UP, DOWN, LEFT, RIGHT, etc.
                        direction_match = re.search(
                            r"(UP|DOWN|LEFT|RIGHT|ORIGIN)", pos_str, re.IGNORECASE
                        )
                        if direction_match:
                            direction = direction_match.group(1).upper()
                            if direction == "UP":
                                position = {"x": 0, "y": 1}
                            elif direction == "DOWN":
                                position = {"x": 0, "y": -1}
                            elif direction == "LEFT":
                                position = {"x": -1, "y": 0}
                            elif direction == "RIGHT":
                                position = {"x": 1, "y": 0}
                            elif direction == "ORIGIN":
                                position = {"x": 0, "y": 0}

                # Extract animations
                animations = []
                animation_matches = re.findall(
                    r"(FadeIn|FadeOut|Write|Transform|GrowFromCenter|MoveTo|Rotate|Scale)[^\n]*",
                    element_block,
                )
                for anim_match in animation_matches:
                    animations.append(
                        {"type": anim_match.split("(")[0], "description": anim_match}
                    )

                # Create the element
                element = VisualElement(
                    element_id=element_id,
                    element_type=element_type,
                    content=content,
                    position=position,
                    animations=animations,
                    layer=j,  # Use index as layer for now
                )

                elements.append(element)

            # Extract timeline
            timeline = []
            timeline_matches = re.findall(
                r"(?:Timeline|Animation sequence)[^\n]*?:(.*?)(?=(?:Timeline|Animation sequence)|$)",
                block,
                re.DOTALL,
            )
            if timeline_matches:
                for timeline_block in timeline_matches:
                    step_matches = re.findall(
                        r"(\d+)[.:]?\s+(.*?)(?=\d+[.:]|\n\n|$)",
                        timeline_block,
                        re.DOTALL,
                    )
                    for step_num, step_desc in step_matches:
                        timeline.append(
                            {
                                "step": int(step_num),
                                "description": step_desc.strip(),
                            }
                        )

            # Create the composition
            composition = VisualComposition(
                composition_id=composition_id,
                title=title,
                elements=elements,
                timeline=timeline,
                duration=sum(element.duration for element in elements),
            )

            compositions.append(composition)

        return compositions

    def _parse_layout_improvements(self, response: str) -> List[Dict[str, Any]]:
        """Parse layout improvements from Claude's response."""

        improvements = []

        # Look for numbered or bulleted improvements
        improvement_matches = re.findall(
            r"(?:\d+[.:]|\*|-)\s+(.*?)(?=(?:\d+[.:]|\*|-)|$)", response, re.DOTALL
        )

        for i, match in enumerate(improvement_matches):
            lines = match.strip().split("\n")
            description = lines[0].strip()

            # Look for code blocks
            code_change = None
            code_block_match = re.search(
                r"```(?:python)?\n(.*?)\n```", match, re.DOTALL
            )
            if code_block_match:
                code_change = code_block_match.group(1).strip()

            # Create the improvement
            improvement = {
                "improvement_id": f"layout_{uuid.uuid4().hex[:8]}",
                "type": "layout",
                "description": description,
                "priority": i + 1,
            }

            if code_change:
                improvement["code_change"] = code_change

            improvements.append(improvement)

        return improvements

    def _parse_animation_improvements(self, response: str) -> List[Dict[str, Any]]:
        """Parse animation improvements from Claude's response."""

        improvements = []

        # Look for numbered or bulleted improvements
        improvement_matches = re.findall(
            r"(?:\d+[.:]|\*|-)\s+(.*?)(?=(?:\d+[.:]|\*|-)|$)", response, re.DOTALL
        )

        for i, match in enumerate(improvement_matches):
            lines = match.strip().split("\n")
            description = lines[0].strip()

            # Look for code blocks
            code_change = None
            code_block_match = re.search(
                r"```(?:python)?\n(.*?)\n```", match, re.DOTALL
            )
            if code_block_match:
                code_change = code_block_match.group(1).strip()

            # Create the improvement
            improvement = {
                "improvement_id": f"animation_{uuid.uuid4().hex[:8]}",
                "type": "animation",
                "description": description,
                "priority": i + 1,
            }

            if code_change:
                improvement["code_change"] = code_change

            improvements.append(improvement)

        return improvements

    def _parse_element_suggestions(self, response: str) -> List[Dict[str, Any]]:
        """Parse element suggestions from Claude's response."""

        suggestions = []

        # Look for numbered or bulleted suggestions
        suggestion_matches = re.findall(
            r"(?:\d+[.:]|\*|-)\s+(.*?)(?=(?:\d+[.:]|\*|-)|$)", response, re.DOTALL
        )

        for i, match in enumerate(suggestion_matches):
            lines = match.strip().split("\n")
            description = lines[0].strip()

            # Look for element type
            element_type = "unknown"
            if "text" in description.lower():
                element_type = "text"
            elif (
                "math" in description.lower()
                or "equation" in description.lower()
                or "formula" in description.lower()
            ):
                element_type = "equation"
            elif (
                "shape" in description.lower()
                or "rectangle" in description.lower()
                or "circle" in description.lower()
            ):
                element_type = "shape"
            elif (
                "graph" in description.lower()
                or "chart" in description.lower()
                or "plot" in description.lower()
            ):
                element_type = "graph"
            elif "image" in description.lower() or "picture" in description.lower():
                element_type = "image"

            # Look for code blocks
            code_example = None
            code_block_match = re.search(
                r"```(?:python)?\n(.*?)\n```", match, re.DOTALL
            )
            if code_block_match:
                code_example = code_block_match.group(1).strip()

            # Create the suggestion
            suggestion = {
                "suggestion_id": f"suggestion_{uuid.uuid4().hex[:8]}",
                "element_type": element_type,
                "description": description,
                "priority": i + 1,
            }

            if code_example:
                suggestion["code_example"] = code_example

            suggestions.append(suggestion)

        return suggestions

    def _extract_enhanced_code(self, response: str, original_code: str) -> str:
        """Extract enhanced code from Claude's response."""

        # Look for code blocks
        code_blocks = re.findall(r"```(?:python)?\n(.*?)\n```", response, re.DOTALL)

        if code_blocks:
            # Use the largest code block (most likely the complete code)
            return max(code_blocks, key=len)

        # If no code block found, return the original code
        return original_code

    def _create_sample_manim_code(self) -> str:
        """Create sample Manim code for testing."""

        return """
from manim import *

class NeuralNetworkScene(Scene):
    def construct(self):
        # Title
        title = Text("Neural Network Basics", font_size=48)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Create a simple neural network
        network = self.create_network()
        self.play(Create(network))
        self.wait(1)
        
        # Show forward propagation
        self.show_forward_propagation(network)
        self.wait(2)
        
        # Conclusion
        conclusion = Text("Deep Learning Foundation", font_size=36)
        conclusion.to_edge(DOWN)
        self.play(FadeIn(conclusion))
        self.wait(1)
    
    def create_network(self):
        # Create layers
        input_layer = self.create_layer(3, LEFT * 4, "Input Layer")
        hidden_layer = self.create_layer(4, ORIGIN, "Hidden Layer")
        output_layer = self.create_layer(2, RIGHT * 4, "Output Layer")
        
        # Group all layers
        network = VGroup(input_layer, hidden_layer, output_layer)
        
        # Add connections between layers
        connections = self.create_connections(input_layer, hidden_layer)
        connections.add(self.create_connections(hidden_layer, output_layer))
        network.add(connections)
        
        return network
    
    def create_layer(self, num_neurons, position, label_text):
        neurons = VGroup()
        for i in range(num_neurons):
            neuron = Circle(radius=0.3, color=BLUE, fill_opacity=0.5)
            neuron.move_to(position + DOWN * (i - (num_neurons-1)/2) * 1.5)
            neurons.add(neuron)
        
        # Add label
        label = Text(label_text, font_size=24)
        label.next_to(neurons, UP, buff=0.5)
        
        layer = VGroup(neurons, label)
        return layer
    
    def create_connections(self, layer1, layer2):
        connections = VGroup()
        neurons1 = layer1[0]  # Get neurons from layer1
        neurons2 = layer2[0]  # Get neurons from layer2
        
        for n1 in neurons1:
            for n2 in neurons2:
                connection = Line(n1.get_center(), n2.get_center(), stroke_opacity=0.3)
                connections.add(connection)
        
        return connections
    
    def show_forward_propagation(self, network):
        input_layer = network[0][0]  # Get neurons from input layer
        hidden_layer = network[1][0]  # Get neurons from hidden layer
        output_layer = network[2][0]  # Get neurons from output layer
        
        # Highlight input
        self.play(input_layer.animate.set_color(GREEN))
        self.wait(0.5)
        
        # Show data flowing to hidden layer
        for neuron in hidden_layer:
            self.play(neuron.animate.set_color(YELLOW), run_time=0.3)
        self.wait(0.5)
        
        # Show data flowing to output layer
        for neuron in output_layer:
            self.play(neuron.animate.set_color(RED), run_time=0.3)
        self.wait(0.5)
"""

    def _create_system_prompt(self) -> str:
        """Create the system prompt for visual composition operations."""

        return """
        You are an expert Visual Composer specializing in Manim animations for educational content.
        
        Your expertise includes:
        1. Analyzing visual elements and their relationships in Manim code
        2. Optimizing layout and positioning for clarity and aesthetics
        3. Coordinating animations and transitions for coherent flow
        4. Balancing visual complexity with educational clarity
        5. Ensuring consistent visual style and theming
        
        When analyzing Manim code:
        - Identify all visual elements (mobjects) and their properties
        - Understand the educational purpose of each element
        - Recognize patterns and relationships between elements
        - Consider the timeline and flow of animations
        - Evaluate the visual hierarchy and focus points
        
        When suggesting improvements:
        - Prioritize educational clarity and conceptual understanding
        - Ensure visual elements support rather than distract from learning
        - Maintain a consistent visual language throughout the animation
        - Consider cognitive load and avoid overwhelming the viewer
        - Use animation to guide attention and emphasize key points
        
        Common visual composition patterns you can apply:
        - Visual grouping of related elements
        - Progressive disclosure of complex concepts
        - Consistent positioning of recurring elements
        - Visual hierarchy through size, color, and position
        - Smooth transitions between scenes and concepts
        
        Be precise, creative, and educational in your visual compositions.
        """
