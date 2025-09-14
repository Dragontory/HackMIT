#!/usr/bin/env python3
"""
Save the rendered video from Modal GPU output
"""

import base64
from pathlib import Path

# This would normally come from the Modal function response
# For now, we'll use a placeholder since we need to extract it from the output


def save_video_from_base64(video_base64: str, filename: str):
    """Save base64 encoded video to local file"""
    try:
        # Create output directory
        output_dir = Path("media/videos")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Decode and save
        video_bytes = base64.b64decode(video_base64)
        output_path = output_dir / filename

        with open(output_path, "wb") as f:
            f.write(video_bytes)

        print(f"✅ Video saved: {output_path}")
        print(f"📏 File size: {len(video_bytes) / (1024*1024):.2f} MB")
        return output_path

    except Exception as e:
        print(f"❌ Error saving video: {e}")
        return None


if __name__ == "__main__":
    print("📥 Video will be saved when we get the base64 data from Modal...")
