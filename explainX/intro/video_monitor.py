#!/usr/bin/env python3
"""
ExplainX Video Monitor
Persistent background service for downloading completed videos
"""

import os
import json
import time
import signal
import sys
from datetime import datetime
from google import genai
from google.genai import types

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class VideoMonitor:
    """Persistent video monitoring service"""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable required")

        self.client = genai.Client(api_key=self.api_key)
        self.pending_file = "pending_downloads.json"
        self.running = True

        # Ensure videos folder exists
        os.makedirs("generated_videos", exist_ok=True)

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        self.running = False

    def _load_pending_tasks(self):
        """Load pending download tasks"""
        if not os.path.exists(self.pending_file):
            return []

        try:
            with open(self.pending_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading pending tasks: {e}")
            return []

    def _save_pending_tasks(self, tasks):
        """Save pending download tasks"""
        try:
            with open(self.pending_file, "w") as f:
                json.dump(tasks, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving pending tasks: {e}")

    def _download_video(self, task):
        """Download a completed video"""
        try:
            operation_name = task["operation_name"]
            educational_context = task["educational_context"]

            print(f"🔍 Checking: {operation_name.split('/')[-1]}")

            # Check if video is ready
            operation = types.GenerateVideosOperation(name=operation_name)
            operation = self.client.operations.get(operation)

            if not operation.done:
                print(f"⏳ Still generating...")
                return False

            if not (operation.response and operation.response.generated_videos):
                print(f"❌ Generation failed - no video in response")
                task["status"] = "failed"
                return True  # Mark as processed

            print(f"🎉 Video ready! Downloading...")

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_context = "".join(
                c if c.isalnum() or c in "-_" else "_" for c in educational_context[:30]
            )
            task_id = operation_name.split("/")[-1]
            filename = f"{timestamp}_{safe_context}_{task_id}.mp4"
            video_path = os.path.join("generated_videos", filename)

            # Download video
            video = operation.response.generated_videos[0]
            self.client.files.download(file=video.video)
            video.video.save(video_path)

            # Get file info
            file_size = os.path.getsize(video_path)
            file_size_mb = file_size / (1024 * 1024)

            print(f"✅ Downloaded: {filename}")
            print(f"📊 Size: {file_size_mb:.2f} MB")

            # Create metadata
            metadata_path = video_path.replace(".mp4", "_info.json")
            metadata = {
                "task_id": task_id,
                "operation_name": operation_name,
                "educational_context": educational_context,
                "downloaded_at": datetime.now().isoformat(),
                "file_size_mb": round(file_size_mb, 2),
                "video_path": video_path,
                "original_task": task,
            }

            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

            task["status"] = "completed"
            task["video_path"] = video_path
            task["completed_at"] = datetime.now().isoformat()

            return True  # Mark as processed

        except Exception as e:
            print(f"💥 Download error: {e}")
            task["status"] = "error"
            task["error"] = str(e)
            return True  # Mark as processed to avoid retry

    def _process_pending_tasks(self):
        """Process all pending download tasks"""
        tasks = self._load_pending_tasks()

        if not tasks:
            return 0

        current_time = datetime.now().timestamp()
        processed_count = 0
        remaining_tasks = []

        for task in tasks:
            if task.get("status") in ["completed", "failed", "error"]:
                continue  # Skip already processed

            # Check if it's time to process this task
            check_after = task.get("check_after", 0)
            if current_time < check_after:
                remaining_tasks.append(task)
                continue

            # Process the task
            print(f"\n📥 Processing: {task['educational_context'][:40]}...")
            processed = self._download_video(task)

            if processed:
                processed_count += 1
                if task.get("status") == "completed":
                    print(f"🏁 Task completed successfully!")
                else:
                    remaining_tasks.append(
                        task
                    )  # Keep failed tasks for potential retry
            else:
                remaining_tasks.append(task)  # Not ready yet

        # Save remaining tasks
        self._save_pending_tasks(remaining_tasks)

        # Check if we should auto-stop (no more pending tasks)
        if processed_count > 0 and len(remaining_tasks) == 0:
            print(f"🏁 All tasks completed! No more pending videos.")
            print(f"🛑 Auto-stopping monitor...")
            self.running = False

        return processed_count

    def run(self):
        """Main monitoring loop"""
        print("🔄 ExplainX Video Monitor Started")
        print("=" * 50)
        print(f"⏰ Checking every 30 seconds")
        print(f"📁 Videos saved to: generated_videos/")
        print(f"💡 Press Ctrl+C to stop")
        print()

        check_count = 0

        while self.running:
            try:
                check_count += 1

                # Show periodic status
                if check_count % 20 == 1:  # Every 10 minutes
                    print(f"💓 Monitor active (check #{check_count})")

                processed = self._process_pending_tasks()

                if processed > 0:
                    print(f"✅ Processed {processed} videos")

                # Wait before next check
                for i in range(30):  # 30 seconds, check every second for shutdown
                    if not self.running:
                        break
                    time.sleep(1)

            except KeyboardInterrupt:
                print(f"\n🛑 Keyboard interrupt received")
                break
            except Exception as e:
                print(f"💥 Monitor error: {e}")
                time.sleep(5)  # Wait before retry

        print(f"🏁 Video Monitor stopped")


def main():
    """Start the video monitor"""
    try:
        monitor = VideoMonitor()
        monitor.run()
    except Exception as e:
        print(f"💥 Failed to start monitor: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
