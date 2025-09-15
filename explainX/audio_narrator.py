# Audio Narrator for Transformer Tutorial
# Generates high-quality educational narration using OpenAI TTS API

import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from openai import AsyncOpenAI
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TransformerAudioNarrator:
    def __init__(self, voice: str = "coral", model: str = "gpt-4o-mini-tts"):
        """
        Initialize the audio narrator for Transformer tutorial

        Args:
            voice: Voice to use for narration (coral, alloy, nova, etc.)
            model: TTS model to use
        """
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.voice = voice
        self.model = model
        self.audio_dir = Path("media/audio")
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    async def generate_scene_audio(
        self, scene_name: str, narration_text: str, instructions: str = None
    ) -> Path:
        """
        Generate audio for a specific scene

        Args:
            scene_name: Name of the scene
            narration_text: Text to be narrated
            instructions: Optional instructions for tone/style

        Returns:
            Path to generated audio file
        """
        if instructions is None:
            instructions = (
                "Speak in a clear, educational tone suitable for learning. "
                "Use appropriate pauses for emphasis and comprehension. "
                "Sound enthusiastic but professional, like a skilled teacher."
            )

        audio_file = self.audio_dir / f"{scene_name}.mp3"

        print(f"🎙️ Generating audio for {scene_name}...")

        try:
            async with self.client.audio.speech.with_streaming_response.create(
                model=self.model,
                voice=self.voice,
                input=narration_text,
                instructions=instructions,
                response_format="mp3",
            ) as response:
                await response.stream_to_file(audio_file)

            print(f"✅ Audio generated: {audio_file}")
            return audio_file

        except Exception as e:
            print(f"❌ Error generating audio for {scene_name}: {e}")
            raise

    def get_scene_narrations(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all narration scripts for the Transformer tutorial scenes

        Returns:
            Dictionary mapping scene names to narration data
        """
        return {
            "intro": {
                "text": """
                Welcome to our comprehensive exploration of "Attention Is All You Need" - 
                the groundbreaking paper that revolutionized artificial intelligence.
                
                Published in 2017 by Vaswani and colleagues at Google, this paper introduced 
                the Transformer architecture... an elegant solution that would become the 
                foundation for GPT, BERT, and virtually every modern language model.
                
                But what made this work so revolutionary? Let's journey through the problems 
                it solved, the mathematics behind it, and why attention truly is all you need.
                
                For decades, sequence modeling relied on recurrent neural networks. But RNNs 
                had a fundamental limitation... they processed information sequentially, 
                word by word, creating a computational bottleneck.
                
                Imagine reading a book where you could only remember the previous sentence. 
                That's the challenge RNNs faced with long sequences. They suffered from 
                vanishing gradients, limited parallelization, and struggled with long-range 
                dependencies.
                
                The Transformer changed everything. By eliminating recurrence entirely and 
                relying purely on attention mechanisms, it achieved superior performance 
                while being dramatically more efficient to train.
                
                Let's see how this revolutionary architecture works.
                """,
                "instructions": (
                    "Speak with excitement and wonder about this breakthrough. "
                    "Use dramatic pauses after key points like 'Transformer architecture' "
                    "and 'attention truly is all you need'. Sound like you're unveiling "
                    "something amazing to students."
                ),
            },
            "attention_math": {
                "text": """
                Now, let's dive deep into the mathematical heart of the Transformer: 
                the attention mechanism.
                
                But first... what IS attention? Think about how you read this very sentence. 
                Your brain doesn't process each word in isolation. When you read the word 'brain', 
                you automatically connect it to 'you' and 'read' - that's attention in action.
                
                Mathematically, attention solves a fundamental question: 
                "Given a query, which parts of the input should I focus on?"
                
                The Transformer implements this through scaled dot-product attention. 
                Here's the elegant formula that changed everything:
                
                Attention of Q, K, V equals softmax of Q times K transpose, divided by 
                square root of d-k, all multiplied by V.
                
                Let's break this down step by step, because understanding this equation 
                is key to understanding modern AI.
                
                First, we need three matrices: Queries, Keys, and Values. Think of this 
                like a sophisticated lookup system. Queries represent "what am I looking for?" 
                Keys represent "what do I contain?" And Values represent "what information 
                do I actually carry?"
                
                Step one: We compute compatibility scores by multiplying Q and K transpose. 
                This tells us how much each query should attend to each key.
                
                Step two: We scale by the square root of d-k. This isn't arbitrary - 
                it's crucial for gradient stability. Without scaling, large dimensions 
                would cause the softmax to saturate, killing gradients.
                
                Step three: We apply softmax to get proper probability distributions. 
                Now each row sums to one, giving us attention weights.
                
                Step four: We multiply by V to get our final output - a weighted 
                combination of all values, where the weights come from our attention scores.
                
                This elegant mechanism allows the model to focus on relevant parts 
                of the input while maintaining differentiability for training.
                """,
                "instructions": (
                    "Speak like a passionate mathematics professor explaining a beautiful theorem. "
                    "Slow down for the main equation and spell out mathematical symbols clearly. "
                    "Use emphasis on key terms like 'queries', 'keys', and 'values'. "
                    "Add longer pauses before each step explanation."
                ),
            },
            "attention_visualization": {
                "text": """
                Now let's see attention in action with concrete examples that will make 
                this abstract concept crystal clear.
                
                Consider two types of attention that power modern AI: self-attention 
                and cross-attention.
                
                In self-attention, each position in a sequence attends to all positions 
                in the SAME sequence. It's like having a conversation with yourself, 
                where every word can influence every other word.
                
                Cross-attention is different. Here, positions in one sequence attend 
                to positions in another sequence. This is crucial for translation, 
                where English words need to attend to their French counterparts.
                
                Let's examine a real sentence: "The quick brown fox jumps over the lazy dog."
                
                Watch what happens when the word "fox" acts as our query. 
                It attends strongly to "quick" and "brown" - its descriptors. 
                It also connects to "jumps" - the action it performs.
                
                When "jumps" becomes our query, it focuses heavily on "fox" - the subject, 
                and "over" - the preposition that follows.
                
                And when "lazy" is our query, it attends most strongly to "dog" - 
                the noun it modifies.
                
                These patterns aren't random. The model learns four key types of attention:
                
                First, syntactic dependencies - like subjects attending to their verbs.
                
                Second, semantic relationships - where related concepts naturally attract.
                
                Third, positional relationships - nearby words often attend to each other.
                
                And fourth, task-specific patterns that emerge based on what the model 
                is trained to do.
                
                This attention matrix visualization shows the full picture. Each cell 
                represents how much one word attends to another. The darker the cell, 
                the stronger the attention. Notice the bidirectional patterns - 
                "cat" and "mat" attend strongly to each other, capturing their semantic relationship.
                """,
                "instructions": (
                    "Use a storytelling tone, as if guiding students through a fascinating discovery. "
                    "Emphasize the word examples with slight pauses before and after. "
                    "When describing the four types of attention, slow down and enumerate clearly. "
                    "Sound amazed when describing the bidirectional patterns."
                ),
            },
            "multihead": {
                "text": """
                But here's where the Transformer gets truly ingenious: instead of using 
                just one attention mechanism, it uses multiple attention "heads" in parallel.
                
                Why multiple heads? Imagine trying to understand a complex conversation 
                where you need to track who's speaking, what they're talking about, 
                and how they feel about it - all simultaneously.
                
                Each attention head specializes in different types of relationships. 
                Some heads focus on syntactic patterns, others on semantic connections, 
                and still others on positional information.
                
                Here's how multi-head attention works mathematically:
                
                We start with our input and create multiple sets of Query, Key, and Value 
                matrices using different learned projections. Each head gets its own 
                W-Q, W-K, and W-V matrices.
                
                Then each head computes attention independently and in parallel. 
                This is where the Transformer's efficiency really shines - 
                all heads can process simultaneously.
                
                Finally, we concatenate all head outputs and multiply by a final 
                output projection matrix W-O. This allows the model to combine 
                insights from all attention heads.
                
                The beauty of this approach is that each head can learn to focus 
                on different aspects of the relationships between words. 
                
                Head one might specialize in subject-verb relationships.
                Head two could focus on adjective-noun connections.
                Head three might capture long-range dependencies.
                And head four could handle positional patterns.
                
                This parallel processing doesn't just improve performance - 
                it dramatically increases the model's capacity to understand 
                complex linguistic relationships without increasing the 
                computational cost per head.
                
                It's like having multiple expert linguists analyze the same text 
                simultaneously, each bringing their specialized knowledge to bear 
                on the problem.
                """,
                "instructions": (
                    "Speak with growing excitement as you explain the multiple heads concept. "
                    "Use analogies with emphasis - 'multiple expert linguists' should sound inspiring. "
                    "Slow down when explaining the mathematical steps. "
                    "Make the parallel processing benefits sound revolutionary."
                ),
            },
            "positional_encoding": {
                "text": """
                Now we encounter a fascinating challenge: how do you teach a model 
                about the ORDER of words without using recurrence?
                
                Traditional RNNs had order built-in through their sequential processing. 
                But the Transformer processes all positions simultaneously. 
                So how does it know that "dog bit man" is different from "man bit dog"?
                
                The answer is positional encoding - one of the most elegant solutions 
                in all of machine learning.
                
                The Transformer uses sinusoidal positional encodings with a beautiful 
                mathematical property. For even dimensions, we use sine functions. 
                For odd dimensions, we use cosine functions.
                
                But this isn't arbitrary. These sine and cosine waves have different 
                frequencies, creating a unique signature for each position.
                
                Position zero gets one pattern, position one gets a slightly different pattern, 
                and so on. Each position receives a unique encoding that the model 
                can learn to interpret.
                
                Look at this positional encoding matrix. Each row represents a position, 
                each column a dimension. The wave-like patterns create a rich, 
                structured representation of order.
                
                These encodings have remarkable properties:
                
                First, they're deterministic - the same position always gets the same encoding.
                
                Second, they capture relative positions through linear relationships.
                
                Third, they're bounded - all values stay within negative one and positive one.
                
                Fourth, they're unique - each position gets a distinct encoding pattern.
                
                And fifth, they allow extrapolation - the model can handle sequences 
                longer than those seen during training.
                
                This elegant solution replaces the sequential processing bottleneck 
                with parallel-friendly position information, maintaining order 
                without sacrificing efficiency.
                """,
                "instructions": (
                    "Start with curiosity and build to appreciation for the elegant solution. "
                    "Emphasize the contrast between 'dog bit man' and 'man bit dog' dramatically. "
                    "When listing the five properties, enumerate them clearly with pauses. "
                    "End with satisfaction about the elegant solution."
                ),
            },
            "architecture": {
                "text": """
                Now let's see how all these components come together in the complete 
                Transformer architecture - a masterpiece of modern AI engineering.
                
                The Transformer consists of two main parts: an encoder and a decoder, 
                each containing multiple identical layers.
                
                Let's start with the encoder. Each encoder layer has two main sub-components:
                
                First, multi-head self-attention, where each position can attend to 
                all positions in the input sequence.
                
                Then, a position-wise feed-forward network that processes each position 
                independently.
                
                Crucially, each sub-component is wrapped with a residual connection 
                and layer normalization. These aren't just implementation details - 
                they're essential for training stability.
                
                The decoder is more complex, with three sub-components per layer:
                
                First, masked multi-head self-attention, where each position can only 
                attend to earlier positions. This prevents the model from "cheating" 
                by looking at future tokens during training.
                
                Second, multi-head cross-attention, where decoder positions attend 
                to encoder outputs. This is where translation magic happens - 
                target language words focus on relevant source language words.
                
                Third, the same position-wise feed-forward network as in the encoder.
                
                Again, each sub-component has residual connections and layer normalization.
                
                The data flow is elegant: input embeddings plus positional encodings 
                flow through the encoder stack, creating rich contextual representations.
                
                These encoder outputs then guide the decoder through cross-attention, 
                while the decoder generates output tokens autoregressively.
                
                Finally, a linear layer and softmax convert the decoder outputs 
                to probability distributions over the vocabulary.
                
                This architecture achieves something remarkable: it maintains the 
                representational power of recurrent networks while enabling 
                massive parallelization during training.
                """,
                "instructions": (
                    "Speak like an architect describing a beautiful building. "
                    "Use clear enumeration for the components: 'First... Second... Third...' "
                    "Emphasize the elegance of the data flow. "
                    "Build excitement toward the 'remarkable achievement' at the end."
                ),
            },
            "training": {
                "text": """
                Training the Transformer required innovation not just in architecture, 
                but in optimization techniques that would unlock its full potential.
                
                The key innovation was the learning rate schedule - a carefully designed 
                warmup followed by decay that proved crucial for stable training.
                
                The schedule increases the learning rate linearly for the first 4,000 steps, 
                then decreases it proportionally to the inverse square root of the step number.
                
                Why this specific schedule? During warmup, the model's parameters are 
                randomly initialized and need gentle guidance. Too high a learning rate 
                initially would cause training to diverge.
                
                After warmup, the model benefits from gradually decreasing learning rates 
                as it fine-tunes its representations.
                
                The training configuration was meticulously designed:
                
                They used the Adam optimizer with specific beta values: 0.9 and 0.98, 
                and epsilon of 10 to the negative 9.
                
                Training took 100,000 steps for the base model and 300,000 for the big model.
                
                They used 8 NVIDIA P100 GPUs, with batch sizes of approximately 
                25,000 source and target tokens.
                
                But hardware wasn't the only consideration. They employed sophisticated 
                regularization techniques.
                
                Dropout, applied throughout the network, randomly zeros out neurons 
                during training to prevent overfitting.
                
                Label smoothing, which softens the target distributions, proved crucial 
                for generalization. Instead of hard one-hot targets, they used 
                slightly smoothed distributions.
                
                These training innovations were just as important as the architectural 
                breakthroughs. Without proper optimization, even the most elegant 
                architecture would fail to realize its potential.
                
                The result? A model that achieved state-of-the-art translation quality 
                while training 10 times faster than previous approaches.
                """,
                "instructions": (
                    "Speak with the precision of a scientist explaining experimental methodology. "
                    "Slow down for the technical numbers and parameters. "
                    "Emphasize the importance of 'training innovations' with conviction. "
                    "End with triumph about the achieved results."
                ),
            },
            "results": {
                "text": """
                The results were nothing short of revolutionary, fundamentally changing 
                how we approach sequence modeling in artificial intelligence.
                
                On English-to-German translation, the Transformer Base model matched 
                the previous state-of-the-art at 27.3 BLEU score. But the Transformer Big 
                model achieved 28.4 BLEU - a new state-of-the-art.
                
                On English-to-French translation, the results were even more impressive. 
                The Transformer Big achieved 41.8 BLEU, surpassing the previous best 
                of 41.0.
                
                But the real revolution wasn't just in accuracy - it was in efficiency.
                
                Previous state-of-the-art models required weeks of training time. 
                The Transformer Big trained in just 3.5 days on 8 P100 GPUs.
                
                This wasn't just faster training - it was a paradigm shift. 
                The massive parallelization capabilities meant researchers could 
                iterate much more quickly, leading to faster scientific progress.
                
                But the impact extended far beyond the original paper. 
                The Transformer became the foundation for the AI revolution we see today.
                
                In 2018, BERT adapted the Transformer encoder for bidirectional 
                language understanding, revolutionizing natural language processing.
                
                GPT-1 used the Transformer decoder for autoregressive language generation, 
                starting the journey toward ChatGPT.
                
                GPT-2 scaled up the approach, showing that bigger Transformers 
                could achieve remarkable capabilities.
                
                GPT-3 demonstrated that scale could lead to emergent abilities 
                like few-shot learning.
                
                Vision Transformers showed that attention could work beyond language, 
                achieving state-of-the-art results in computer vision.
                
                And GPT-4 brought us to the era of large language models that can 
                converse, reason, and assist with complex tasks.
                
                From protein folding prediction to code generation, from image recognition 
                to creative writing - the Transformer architecture now powers 
                virtually every breakthrough in AI.
                
                The paper's impact is measured not just in citations - over 50,000 and counting - 
                but in the fundamental transformation of entire industries.
                """,
                "instructions": (
                    "Start with celebration and build to awe. "
                    "Emphasize the BLEU score improvements with precision. "
                    "When listing the model progression (BERT, GPT-1, etc.), build momentum. "
                    "End with wonder at the broad impact across industries."
                ),
            },
            "conclusion": {
                "text": """
                As we reach the end of our journey through "Attention Is All You Need", 
                let's reflect on what makes this work truly revolutionary.
                
                The Transformer didn't just solve a technical problem - it revealed 
                a fundamental truth about intelligence and computation.
                
                The key insight was elegantly simple: you don't need recurrence to model sequences. 
                You don't need convolution to capture relationships. 
                You just need attention.
                
                By allowing every position to attend to every other position, 
                the Transformer captured global dependencies in constant time. 
                This wasn't just an engineering improvement - it was a conceptual breakthrough.
                
                The innovations we've explored - scaled dot-product attention, 
                multi-head mechanisms, positional encoding, the encoder-decoder architecture - 
                each solved specific challenges with mathematical elegance.
                
                But perhaps the most remarkable aspect is how these innovations have scaled. 
                The principles from this 2017 paper still govern the largest AI models today.
                
                From 65 million parameters in the original Transformer to over 1 trillion 
                in modern models, the architecture has proven remarkably scalable.
                
                The efficiency gains - 90% reduction in training costs while achieving 
                better performance - democratized AI research and accelerated progress 
                across the entire field.
                
                Looking forward, the Transformer continues to evolve. Researchers are 
                developing sparse attention patterns for longer sequences, 
                multimodal fusion for vision and language, and specialized architectures 
                for specific domains.
                
                Yet the core insight remains: attention is indeed all you need.
                
                This simple but profound idea - that intelligence emerges from the ability 
                to selectively focus on relevant information - has become the foundation 
                of modern artificial intelligence.
                
                From the algorithm that powers your search results to the AI assistant 
                that helps you write code, from the system that translates languages 
                to the model that generates art - they all trace their lineage back 
                to this elegant paper.
                
                "Attention Is All You Need" - six words that changed everything.
                
                Thank you for joining this exploration of one of the most important 
                papers in the history of artificial intelligence.
                """,
                "instructions": (
                    "Speak with deep appreciation and wonder, like concluding a profound lecture. "
                    "Emphasize 'Attention Is All You Need' as the key insight. "
                    "Build emotion toward the end about the paper's lasting impact. "
                    "End with gratitude and a sense of completion."
                ),
            },
        }

    async def generate_all_audio(self) -> Dict[str, Path]:
        """
        Generate audio for all scenes in the tutorial

        Returns:
            Dictionary mapping scene names to audio file paths
        """
        narrations = self.get_scene_narrations()
        audio_files = {}

        print(f"🎙️ Generating audio for {len(narrations)} scenes...")

        # Generate audio for each scene
        tasks = []
        for scene_name, narration_data in narrations.items():
            task = self.generate_scene_audio(
                scene_name, narration_data["text"], narration_data.get("instructions")
            )
            tasks.append((scene_name, task))

        # Wait for all audio generation to complete
        for scene_name, task in tasks:
            try:
                audio_file = await task
                audio_files[scene_name] = audio_file
            except Exception as e:
                print(f"❌ Failed to generate audio for {scene_name}: {e}")

        print(f"✅ Generated audio for {len(audio_files)} scenes")
        return audio_files

    def combine_video_with_audio(
        self, video_path: Path, audio_path: Path, output_path: Path
    ) -> bool:
        """
        Combine video with audio using ffmpeg

        Args:
            video_path: Path to input video file
            audio_path: Path to input audio file
            output_path: Path to output video with audio

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = [
                "ffmpeg",
                "-y",  # Overwrite output
                "-i",
                str(video_path),  # Input video
                "-i",
                str(audio_path),  # Input audio
                "-c:v",
                "copy",  # Copy video stream
                "-c:a",
                "aac",  # Encode audio as AAC
                "-map",
                "0:v:0",  # Map video from first input
                "-map",
                "1:a:0",  # Map audio from second input
                "-shortest",  # End when shortest stream ends
                str(output_path),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Combined video with audio: {output_path}")
                return True
            else:
                print(f"❌ FFmpeg error: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Error combining video with audio: {e}")
            return False


async def main():
    """Main function to demonstrate audio generation"""
    narrator = TransformerAudioNarrator()

    # Generate audio for all scenes
    audio_files = await narrator.generate_all_audio()

    # Example: Combine with existing video
    video_path = Path("media/videos/TransformerArchitectureIntro.mp4")
    if video_path.exists() and "intro" in audio_files:
        output_path = Path("media/videos/TransformerArchitectureIntro_with_audio.mp4")
        narrator.combine_video_with_audio(video_path, audio_files["intro"], output_path)
        print(f"🎬 Video with audio created: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
