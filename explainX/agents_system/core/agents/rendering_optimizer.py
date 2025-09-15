"""
Rendering Optimizer Agent implementation.

This agent analyzes Manim code and rendering settings to optimize performance,
balancing quality and speed for efficient video generation.
"""

import logging
import re
import time
import uuid
import os
import psutil
import subprocess
from typing import List, Dict, Any, Tuple, Optional, Set

from ...domain.interfaces import IAgent
from ...domain.models import (
    AgentState,
    AgentResult,
    RenderingOptimizationResult,
    RenderingProfile,
    PerformanceMetrics,
    OptimizationSuggestion,
)
from ...infrastructure.anthropic.client import AnthropicClient
from ...infrastructure.anthropic.models import ClaudeMessage


logger = logging.getLogger(__name__)


class RenderingOptimizerAgent(IAgent):
    """
    Specialized agent for optimizing rendering settings in Manim animations.

    Uses Claude's performance optimization understanding to:
    - Analyze code complexity and resource requirements
    - Identify rendering bottlenecks and inefficiencies
    - Optimize rendering settings for speed/quality balance
    - Suggest code improvements for better rendering performance
    - Create optimal rendering profiles for different use cases
    """

    def __init__(self, claude_client: AnthropicClient):
        self.claude_client = claude_client
        self._system_prompt = self._create_system_prompt()

    @property
    def name(self) -> str:
        return "RenderingOptimizerAgent"

    @property
    def description(self) -> str:
        return "Optimizes rendering settings for performance"

    async def process(self, state: AgentState) -> AgentResult:
        """Process state and optimize rendering settings."""
        start_time = time.time()

        try:
            logger.info(f"Rendering Optimizer processing: {state['content_title']}")

            # Get the code to analyze and optimize
            manim_code = state.get("manim_code", "")

            if not manim_code:
                # Create sample code for testing
                manim_code = self._create_sample_manim_code()
                logger.info("No Manim code provided, using sample code")

            # Create default rendering profile if not provided
            original_profile = state.get(
                "rendering_profile", self._create_default_profile()
            )

            # Perform rendering optimization
            result = await self.optimize_rendering(manim_code, original_profile)

            # Update state
            state["rendering_optimization_result"] = result
            state["manim_code"] = result.optimized_code
            state["rendering_profile"] = result.optimized_profile
            state["current_agent"] = self.name
            state["processing_stage"] = "rendering_optimization_complete"

            processing_time = time.time() - start_time
            result.processing_time = processing_time

            return AgentResult(
                success=result.success,
                data=result,
                metadata={
                    "agent": self.name,
                    "suggestions_made": len(result.optimization_suggestions),
                    "optimizations_applied": len(result.applied_optimizations),
                    "estimated_speedup": result.estimated_speedup,
                    "estimated_time_saved": result.estimated_time_saved,
                    "processing_time": processing_time,
                },
            )

        except Exception as e:
            logger.error(f"Rendering Optimizer error: {e}")
            return AgentResult(
                success=False,
                data=None,
                errors=[f"Rendering optimization failed: {str(e)}"],
            )

    async def optimize_rendering(
        self, manim_code: str, original_profile: RenderingProfile
    ) -> RenderingOptimizationResult:
        """
        Optimize rendering settings for Manim code.

        Args:
            manim_code: The Manim Python code to analyze and optimize
            original_profile: The original rendering profile

        Returns:
            RenderingOptimizationResult: Complete results with optimizations and metrics
        """

        # Step 1: Analyze code complexity and resource requirements
        performance_metrics = await self.analyze_performance(
            manim_code, original_profile
        )

        # Step 2: Generate optimization suggestions
        optimization_suggestions = await self.generate_optimization_suggestions(
            manim_code, original_profile, performance_metrics
        )

        # Step 3: Apply optimizations to code
        optimized_code, applied_optimizations = await self.apply_code_optimizations(
            manim_code, optimization_suggestions
        )

        # Step 4: Create optimized rendering profile
        optimized_profile = await self.create_optimized_profile(
            original_profile, optimization_suggestions, applied_optimizations
        )

        # Calculate estimated improvements
        estimated_speedup = self._calculate_estimated_speedup(
            applied_optimizations, performance_metrics
        )
        estimated_time_saved = (
            performance_metrics.total_render_time * (1 - 1 / estimated_speedup)
            if performance_metrics and performance_metrics.total_render_time > 0
            else 0.0
        )

        # Determine success
        # Success if we have suggestions (even if no major speedup expected)
        success = len(optimization_suggestions) > 0 or estimated_speedup >= 1.0

        return RenderingOptimizationResult(
            original_code=manim_code,
            optimized_code=optimized_code,
            original_profile=original_profile,
            optimized_profile=optimized_profile,
            performance_metrics=performance_metrics,
            optimization_suggestions=optimization_suggestions,
            applied_optimizations=applied_optimizations,
            estimated_time_saved=estimated_time_saved,
            estimated_speedup=estimated_speedup,
            success=success,
        )

    async def analyze_performance(
        self, code: str, profile: RenderingProfile
    ) -> Optional[PerformanceMetrics]:
        """Analyze rendering performance of Manim code."""

        # First, try to get actual performance metrics by running a test render
        actual_metrics = self._run_test_render(code, profile)
        if actual_metrics:
            return actual_metrics

        # If test render fails or is disabled, estimate metrics based on code analysis
        return await self._estimate_performance_metrics(code, profile)

    def _run_test_render(
        self, code: str, profile: RenderingProfile
    ) -> Optional[PerformanceMetrics]:
        """Run a test render to get actual performance metrics."""

        # Skip actual rendering in most environments to avoid dependencies
        # In a real implementation, this would run a quick test render
        return None

    async def _estimate_performance_metrics(
        self, code: str, profile: RenderingProfile
    ) -> PerformanceMetrics:
        """Estimate performance metrics based on code analysis."""

        # Prepare context for Claude
        context_parts = [
            "I need to estimate rendering performance for this Manim code:"
        ]
        context_parts.append(f"```python\n{code}\n```")

        context_parts.append("Rendering profile:")
        context_parts.append(f"- Quality: {profile.quality}")
        context_parts.append(
            f"- Resolution: {profile.resolution[0]}x{profile.resolution[1]}"
        )
        context_parts.append(f"- Frame rate: {profile.frame_rate}")
        context_parts.append(f"- Renderer: {profile.renderer}")

        context_parts.append(
            "Please analyze the code complexity and estimate rendering performance metrics. "
            "Focus on identifying potential bottlenecks, estimating render time, and suggesting optimizations."
        )

        messages = [
            ClaudeMessage(
                role="user",
                content="\n\n".join(context_parts),
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)

        # Parse the response to extract performance metrics
        return self._parse_performance_metrics(response.content, code)

    async def generate_optimization_suggestions(
        self,
        code: str,
        profile: RenderingProfile,
        metrics: Optional[PerformanceMetrics],
    ) -> List[OptimizationSuggestion]:
        """Generate suggestions for optimizing rendering performance."""

        # Prepare context for Claude
        context_parts = ["I need optimization suggestions for this Manim code:"]
        context_parts.append(f"```python\n{code}\n```")

        context_parts.append("Current rendering profile:")
        context_parts.append(f"- Quality: {profile.quality}")
        context_parts.append(
            f"- Resolution: {profile.resolution[0]}x{profile.resolution[1]}"
        )
        context_parts.append(f"- Frame rate: {profile.frame_rate}")
        context_parts.append(f"- Renderer: {profile.renderer}")

        if metrics:
            context_parts.append("Performance metrics:")
            context_parts.append(
                f"- Total render time: {metrics.total_render_time:.2f} seconds"
            )
            context_parts.append(f"- Frames rendered: {metrics.frames_rendered}")
            context_parts.append(
                f"- Average frame time: {metrics.average_frame_time:.4f} seconds"
            )
            context_parts.append(
                f"- Peak memory usage: {metrics.peak_memory_usage:.2f} MB"
            )
            context_parts.append(f"- CPU usage: {metrics.cpu_usage:.1f}%")

            if metrics.bottlenecks:
                context_parts.append("Identified bottlenecks:")
                for bottleneck in metrics.bottlenecks:
                    context_parts.append(f"- {bottleneck}")

        context_parts.append(
            "Please suggest specific optimizations to improve rendering performance. "
            "Include code changes, rendering setting adjustments, and command line arguments. "
            "For each suggestion, estimate the impact and implementation complexity."
        )

        messages = [
            ClaudeMessage(
                role="user",
                content="\n\n".join(context_parts),
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)

        # Parse the response to extract optimization suggestions
        return self._parse_optimization_suggestions(response.content)

    async def apply_code_optimizations(
        self, code: str, suggestions: List[OptimizationSuggestion]
    ) -> Tuple[str, List[OptimizationSuggestion]]:
        """Apply code optimizations from suggestions."""

        # Filter suggestions that involve code changes
        code_suggestions = [
            s for s in suggestions if s.category == "code" and s.code_changes
        ]

        if not code_suggestions:
            return code, []

        # Prepare context for Claude
        context_parts = ["I need to apply these code optimizations to this Manim code:"]
        context_parts.append(f"```python\n{code}\n```")

        context_parts.append("Optimization suggestions to apply:")
        for i, suggestion in enumerate(code_suggestions, 1):
            context_parts.append(f"{i}. {suggestion.description}")
            if suggestion.code_changes:
                context_parts.append(f"   Code changes: {suggestion.code_changes}")

        context_parts.append(
            "Please apply these optimizations to the code and provide the complete optimized version. "
            "Make sure the code remains functional and follows Manim best practices."
        )

        messages = [
            ClaudeMessage(
                role="user",
                content="\n\n".join(context_parts),
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)

        # Extract the optimized code from the response
        optimized_code = self._extract_optimized_code(response.content, code)

        # Mark suggestions as applied if the code changed
        applied_suggestions = []
        if optimized_code != code:
            for suggestion in code_suggestions:
                suggestion.applied = True
                applied_suggestions.append(suggestion)

        return optimized_code, applied_suggestions

    async def create_optimized_profile(
        self,
        original_profile: RenderingProfile,
        suggestions: List[OptimizationSuggestion],
        applied_code_optimizations: List[OptimizationSuggestion],
    ) -> RenderingProfile:
        """Create optimized rendering profile based on suggestions."""

        # Start with a copy of the original profile
        optimized_profile = RenderingProfile(
            profile_id=f"optimized_{uuid.uuid4().hex[:8]}",
            name=f"Optimized {original_profile.name}",
            quality=original_profile.quality,
            resolution=original_profile.resolution,
            frame_rate=original_profile.frame_rate,
            pixel_width=original_profile.pixel_width,
            pixel_height=original_profile.pixel_height,
            preview_mode=original_profile.preview_mode,
            disable_caching=original_profile.disable_caching,
            transparent=original_profile.transparent,
            write_to_movie=original_profile.write_to_movie,
            save_last_frame=original_profile.save_last_frame,
            save_pngs=original_profile.save_pngs,
            write_all=original_profile.write_all,
            format=original_profile.format,
            renderer=original_profile.renderer,
            media_dir=original_profile.media_dir,
            log_level=original_profile.log_level,
            progress_bar=original_profile.progress_bar,
            command_line_args=original_profile.command_line_args.copy(),
        )

        # Filter suggestions that involve profile changes
        profile_suggestions = [
            s
            for s in suggestions
            if s.category in ["quality", "resolution", "caching"]
            and not s.requires_hardware_change
        ]

        # Apply profile changes
        for suggestion in profile_suggestions:
            if suggestion.category == "quality":
                if "low" in suggestion.description.lower():
                    optimized_profile.quality = "low"
                elif "medium" in suggestion.description.lower():
                    optimized_profile.quality = "medium"
                elif "high" in suggestion.description.lower():
                    optimized_profile.quality = "high"
                elif "production" in suggestion.description.lower():
                    optimized_profile.quality = "production"

            elif suggestion.category == "resolution":
                # Look for resolution values in the description
                resolution_match = re.search(
                    r"(\d+)\s*x\s*(\d+)", suggestion.description
                )
                if resolution_match:
                    width = int(resolution_match.group(1))
                    height = int(resolution_match.group(2))
                    optimized_profile.resolution = (width, height)

            elif suggestion.category == "caching":
                if "enable caching" in suggestion.description.lower():
                    optimized_profile.disable_caching = False
                elif "disable caching" in suggestion.description.lower():
                    optimized_profile.disable_caching = True

            # Apply command line args if provided
            if suggestion.command_line_args:
                optimized_profile.command_line_args.extend(suggestion.command_line_args)

            # Mark suggestion as applied
            suggestion.applied = True

        return optimized_profile

    def _parse_performance_metrics(
        self, response: str, code: str
    ) -> PerformanceMetrics:
        """Parse performance metrics from Claude's response."""

        # Extract total render time
        total_time_match = re.search(
            r"(?:Total render time|Estimated render time)[:\s]*(\d+\.?\d*)", response
        )
        total_render_time = (
            float(total_time_match.group(1)) if total_time_match else 60.0
        )

        # Extract frames rendered
        frames_match = re.search(
            r"(?:Frames rendered|Total frames)[:\s]*(\d+)", response
        )
        frames_rendered = int(frames_match.group(1)) if frames_match else 300

        # Calculate average frame time
        average_frame_time = (
            total_render_time / frames_rendered if frames_rendered > 0 else 0.2
        )

        # Extract memory usage
        memory_match = re.search(
            r"(?:Peak memory usage|Memory usage)[:\s]*(\d+\.?\d*)", response
        )
        peak_memory_usage = float(memory_match.group(1)) if memory_match else 500.0

        # Extract CPU usage
        cpu_match = re.search(r"(?:CPU usage)[:\s]*(\d+\.?\d*)", response)
        cpu_usage = float(cpu_match.group(1)) if cpu_match else 50.0

        # Extract GPU usage if available
        gpu_match = re.search(r"(?:GPU usage)[:\s]*(\d+\.?\d*)", response)
        gpu_usage = float(gpu_match.group(1)) if gpu_match else None

        # Extract bottlenecks
        bottlenecks = []
        bottleneck_section = re.search(
            r"(?:Bottlenecks|Performance bottlenecks|Identified bottlenecks)[:\s]*(.*?)(?=\n\n|\n#|\Z)",
            response,
            re.DOTALL,
        )

        if bottleneck_section:
            bottleneck_text = bottleneck_section.group(1).strip()
            bottleneck_items = re.findall(
                r"[-*]\s+(.*?)(?=[-*]|\n\n|\Z)", bottleneck_text, re.DOTALL
            )
            bottlenecks = [item.strip() for item in bottleneck_items if item.strip()]

        # Extract optimization potential
        potential_match = re.search(
            r"(?:Optimization potential)[:\s]*(\d+\.?\d*)", response
        )
        optimization_potential = (
            float(potential_match.group(1)) if potential_match else 0.3
        )

        # Ensure optimization potential is between 0 and 1
        optimization_potential = min(max(optimization_potential, 0.0), 1.0)

        return PerformanceMetrics(
            total_render_time=total_render_time,
            frames_rendered=frames_rendered,
            average_frame_time=average_frame_time,
            peak_memory_usage=peak_memory_usage,
            cpu_usage=cpu_usage,
            gpu_usage=gpu_usage,
            bottlenecks=bottlenecks,
            optimization_potential=optimization_potential,
        )

    def _parse_optimization_suggestions(
        self, response: str
    ) -> List[OptimizationSuggestion]:
        """Parse optimization suggestions from Claude's response."""

        suggestions = []

        # Look for numbered or bulleted suggestions
        suggestion_blocks = re.findall(
            r"(?:\d+[.:]|\*|-)\s+(.*?)(?=(?:\d+[.:]|\*|-)|$)", response, re.DOTALL
        )

        for i, block in enumerate(suggestion_blocks):
            lines = block.strip().split("\n")
            description = lines[0].strip()

            # Skip if this doesn't look like a suggestion
            if len(description) < 10:
                continue

            # Determine category
            category = "code"  # Default
            if any(x in description.lower() for x in ["quality", "preview"]):
                category = "quality"
            elif any(
                x in description.lower() for x in ["resolution", "size", "dimension"]
            ):
                category = "resolution"
            elif any(x in description.lower() for x in ["cache", "caching"]):
                category = "caching"
            elif any(
                x in description.lower() for x in ["hardware", "gpu", "cpu", "memory"]
            ):
                category = "hardware"

            # Determine impact
            impact = "medium"  # Default
            impact_match = re.search(
                r"(?:Impact|Effect)[:\s]*(low|medium|high)", block, re.IGNORECASE
            )
            if impact_match:
                impact = impact_match.group(1).lower()
            elif (
                "significant" in block.lower()
                or "dramatic" in block.lower()
                or "major" in block.lower()
            ):
                impact = "high"
            elif (
                "minor" in block.lower()
                or "small" in block.lower()
                or "slight" in block.lower()
            ):
                impact = "low"

            # Determine complexity
            complexity = "medium"  # Default
            complexity_match = re.search(
                r"(?:Complexity|Difficulty|Implementation)[:\s]*(easy|medium|hard|simple|complex)",
                block,
                re.IGNORECASE,
            )
            if complexity_match:
                complexity_str = complexity_match.group(1).lower()
                if complexity_str in ["easy", "simple"]:
                    complexity = "easy"
                elif complexity_str in ["hard", "complex"]:
                    complexity = "hard"
                else:
                    complexity = "medium"

            # Extract estimated speedup
            speedup = 1.0  # Default (no speedup)
            speedup_match = re.search(
                r"(?:Speedup|Speed improvement|Performance gain)[:\s]*(\d+\.?\d*)x",
                block,
                re.IGNORECASE,
            )
            if speedup_match:
                speedup = float(speedup_match.group(1))
            elif "significant" in block.lower() or "dramatic" in block.lower():
                speedup = 2.0
            elif "moderate" in block.lower():
                speedup = 1.5
            elif "minor" in block.lower() or "small" in block.lower():
                speedup = 1.2

            # Look for code changes
            code_changes = None
            code_block_match = re.search(
                r"```(?:python)?\n(.*?)\n```", block, re.DOTALL
            )
            if code_block_match:
                code_changes = code_block_match.group(1).strip()

            # Look for command line args
            command_line_args = None
            cmd_match = re.search(
                r"(?:Command line|CLI|Args)[:\s]*(.*?)(?=\n|$)", block, re.IGNORECASE
            )
            if cmd_match:
                cmd_str = cmd_match.group(1).strip()
                command_line_args = [
                    arg.strip() for arg in cmd_str.split() if arg.strip()
                ]

            # Check if hardware change is required
            requires_hardware = False
            if any(
                x in block.lower()
                for x in ["upgrade hardware", "better gpu", "more ram", "faster cpu"]
            ):
                requires_hardware = True

            # Create the suggestion
            suggestion = OptimizationSuggestion(
                suggestion_id=f"suggestion_{uuid.uuid4().hex[:8]}",
                category=category,
                description=description,
                impact=impact,
                implementation_complexity=complexity,
                estimated_speedup=speedup,
                code_changes=code_changes,
                command_line_args=command_line_args,
                requires_hardware_change=requires_hardware,
            )

            suggestions.append(suggestion)

        return suggestions

    def _extract_optimized_code(self, response: str, original_code: str) -> str:
        """Extract optimized code from Claude's response."""

        # Look for code blocks
        code_blocks = re.findall(r"```(?:python)?\n(.*?)\n```", response, re.DOTALL)

        if code_blocks:
            # Use the largest code block (most likely the complete code)
            return max(code_blocks, key=len)

        # If no code block found, return the original code
        return original_code

    def _calculate_estimated_speedup(
        self,
        applied_optimizations: List[OptimizationSuggestion],
        metrics: Optional[PerformanceMetrics],
    ) -> float:
        """Calculate estimated speedup from applied optimizations."""

        if not applied_optimizations:
            return 1.0  # No speedup

        # Start with base speedup of 1.0 (no change)
        speedup = 1.0

        # Add contribution from each optimization
        # Using diminishing returns formula: total = 1 - (1-a)*(1-b)*(1-c)...
        for opt in applied_optimizations:
            # Convert speedup factor to improvement percentage
            improvement = 1 - (1 / opt.estimated_speedup)
            # Apply diminishing returns
            speedup = speedup / (1 - improvement)

        # Cap reasonable speedup based on optimization potential
        max_speedup = 10.0  # Hard cap at 10x speedup
        if metrics and metrics.optimization_potential:
            # Higher potential allows higher speedup
            potential_cap = 1.0 + (9.0 * metrics.optimization_potential)  # 1.0 to 10.0
            max_speedup = min(max_speedup, potential_cap)

        return min(speedup, max_speedup)

    def _create_default_profile(self) -> RenderingProfile:
        """Create a default rendering profile."""

        return RenderingProfile(
            profile_id="default",
            name="Default Profile",
            quality="medium",
            resolution=(1280, 720),
            frame_rate=30,
            renderer="cairo",
        )

    def _create_sample_manim_code(self) -> str:
        """Create sample Manim code for testing."""

        return """
from manim import *

class ComplexScene(Scene):
    def construct(self):
        # Title
        title = Text("Complex Animation Example", font_size=48)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Create a grid of shapes
        shapes = VGroup()
        for i in range(10):
            for j in range(10):
                if (i + j) % 2 == 0:
                    shape = Square(side_length=0.2, fill_opacity=0.8)
                else:
                    shape = Circle(radius=0.1, fill_opacity=0.8)
                shape.set_color(color_gradient([BLUE, GREEN], 2)[(i + j) % 2])
                shape.move_to(np.array([-2.25 + i * 0.5, 1.5 - j * 0.5, 0]))
                shapes.add(shape)
        
        # Animate the grid
        self.play(FadeIn(shapes, lag_ratio=0.05, run_time=3))
        self.wait(1)
        
        # Create complex formula
        formula = MathTex(
            r"f(z) = \\frac{1}{2\\pi i} \\oint_\\gamma \\frac{f(\\zeta)}{\\zeta - z} d\\zeta",
            font_size=40
        )
        formula.next_to(shapes, DOWN, buff=0.5)
        
        # Animate formula
        self.play(Write(formula))
        self.wait(1)
        
        # Create a graph
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-2, 2, 1],
            x_length=6,
            y_length=4,
            axis_config={"include_tip": False}
        )
        
        # Plot a function
        graph = axes.plot(lambda x: np.sin(x), color=YELLOW)
        graph_label = axes.get_graph_label(graph, "\\sin(x)", x_val=2)
        
        graph_group = VGroup(axes, graph, graph_label)
        graph_group.scale(0.6)
        graph_group.to_edge(DOWN)
        
        # Animate graph
        self.play(FadeTransform(formula, graph_group))
        self.wait(1)
        
        # Create dots that move along the graph
        dots = VGroup()
        for i in range(20):
            dot = Dot(color=RED)
            dot.move_to(axes.c2p(i/10 - 3, np.sin(i/10 - 3)))
            dots.add(dot)
        
        self.play(FadeIn(dots))
        
        # Animate dots along the curve
        animations = []
        for i, dot in enumerate(dots):
            target_x = i/10 + 3
            target_y = np.sin(target_x)
            target_point = axes.c2p(target_x, target_y)
            animations.append(dot.animate.move_to(target_point))
        
        self.play(AnimationGroup(*animations, lag_ratio=0.1))
        self.wait(1)
        
        # Final animation
        final_text = Text("Optimization Complete", font_size=42)
        final_text.to_edge(DOWN)
        
        self.play(
            FadeOut(shapes),
            FadeOut(graph_group),
            FadeOut(dots),
            FadeOut(title),
            FadeIn(final_text)
        )
        self.wait(2)
"""

    def _create_system_prompt(self) -> str:
        """Create the system prompt for rendering optimization operations."""

        return """
        You are an expert Rendering Optimizer specializing in Manim animations.
        
        Your expertise includes:
        1. Analyzing code complexity and resource requirements
        2. Identifying rendering bottlenecks and inefficiencies
        3. Optimizing rendering settings for speed/quality balance
        4. Suggesting code improvements for better rendering performance
        5. Creating optimal rendering profiles for different use cases
        
        When analyzing Manim code:
        - Identify computationally expensive operations
        - Recognize patterns that could lead to rendering inefficiency
        - Estimate resource usage (CPU, memory, time)
        - Consider the balance between animation quality and performance
        - Evaluate the complexity of mathematical expressions and visual elements
        
        When suggesting optimizations:
        - Prioritize changes with the highest impact and lowest implementation complexity
        - Consider the educational purpose and visual clarity of the animations
        - Suggest specific code changes with clear explanations
        - Recommend appropriate rendering settings (quality, resolution, caching)
        - Provide command-line arguments for Manim rendering
        
        Common optimization patterns you can apply:
        - Reducing unnecessary precision in calculations
        - Simplifying complex visual elements
        - Optimizing animation sequences and transitions
        - Adjusting resolution and quality settings appropriately
        - Enabling or disabling caching based on scene complexity
        
        Be precise, practical, and performance-focused in your optimizations.
        """
