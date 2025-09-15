#!/bin/bash
# ExplainX Video Monitor Starter Script

echo "🚀 Starting ExplainX Video Monitor..."

# Create logs directory
mkdir -p logs

# Start monitor in background with logging
nohup python video_monitor.py > logs/monitor.log 2>&1 &

# Get the process ID
MONITOR_PID=$!

echo "✅ Video Monitor started!"
echo "🆔 Process ID: $MONITOR_PID"
echo "📁 Logs: logs/monitor.log"
echo "🛑 To stop: kill $MONITOR_PID"

# Save PID for easy stopping
echo $MONITOR_PID > monitor.pid

echo "💡 Monitor is now running independently"
echo "📹 Videos will be automatically downloaded to: generated_videos/"
