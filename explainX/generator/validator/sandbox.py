"""
Process limits and temp directories for sandboxed execution.
"""

import os
import signal
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Optional, Tuple, List, Dict


class SandboxLimits:
    """Resource limits for sandboxed execution."""

    def __init__(
        self,
        timeout_seconds: int = 30,
        max_memory_mb: int = 512,
        max_output_size: int = 1024 * 1024,  # 1MB
        max_files: int = 100,
    ):
        self.timeout_seconds = timeout_seconds
        self.max_memory_mb = max_memory_mb
        self.max_output_size = max_output_size
        self.max_files = max_files


class SandboxEnvironment:
    """Manages sandboxed execution environment."""

    def __init__(self, limits: SandboxLimits = None):
        self.limits = limits or SandboxLimits()
        self.temp_dir: Optional[Path] = None

    def __enter__(self):
        """Set up temporary directory."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="manim_sandbox_"))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up temporary directory."""
        if self.temp_dir and self.temp_dir.exists():
            self._cleanup_directory(self.temp_dir)

    def execute_command(
        self,
        command: List[str],
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, str, str]:
        """
        Execute command with resource limits.
        Returns (exit_code, stdout, stderr).
        """
        if cwd is None:
            cwd = self.temp_dir

        # Set up environment variables
        execution_env = os.environ.copy()
        execution_env["MANIMGL_LOG_LEVEL"] = "ERROR"  # Reduce Manim logging
        execution_env["TMPDIR"] = str(self.temp_dir)

        # Merge provided environment variables
        if env:
            execution_env.update(env)

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(cwd),
                env=execution_env,
                text=True,
                preexec_fn=self._set_process_limits,
            )

            # Use timeout
            try:
                stdout, stderr = process.communicate(
                    timeout=self.limits.timeout_seconds
                )
                exit_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                exit_code = -1
                stderr = (
                    f"Process timed out after {self.limits.timeout_seconds} seconds\n"
                    + stderr
                )

            # Truncate output if too large
            if len(stdout) > self.limits.max_output_size:
                stdout = stdout[: self.limits.max_output_size] + "\n[OUTPUT TRUNCATED]"

            if len(stderr) > self.limits.max_output_size:
                stderr = (
                    stderr[: self.limits.max_output_size] + "\n[ERROR OUTPUT TRUNCATED]"
                )

            return exit_code, stdout, stderr

        except Exception as e:
            return -1, "", f"Failed to execute command: {e}"

    def write_file(self, filename: str, content: str) -> Path:
        """Write content to a file in the sandbox."""
        if not self.temp_dir:
            raise RuntimeError("Sandbox not initialized")

        file_path = self.temp_dir / filename

        # Check file count limit
        existing_files = list(self.temp_dir.rglob("*"))
        if len(existing_files) >= self.limits.max_files:
            raise RuntimeError(
                f"File limit exceeded: {len(existing_files)} >= {self.limits.max_files}"
            )

        file_path.write_text(content, encoding="utf-8")
        return file_path

    def get_temp_dir(self) -> Path:
        """Get the temporary directory path."""
        if not self.temp_dir:
            raise RuntimeError("Sandbox not initialized")
        return self.temp_dir

    def _set_process_limits(self):
        """Set resource limits for child process."""
        try:
            import resource

            # Set memory limit (in bytes)
            memory_limit = self.limits.max_memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))

            # Set CPU time limit
            cpu_limit = self.limits.timeout_seconds
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))

            # Limit number of processes
            resource.setrlimit(resource.RLIMIT_NPROC, (10, 10))

            # Limit number of open files
            resource.setrlimit(resource.RLIMIT_NOFILE, (50, 50))

        except ImportError:
            # resource module not available (Windows)
            pass
        except Exception:
            # Ignore errors setting limits - execution will still be time-bounded
            pass

    def _cleanup_directory(self, directory: Path):
        """Recursively clean up directory."""
        try:
            import shutil

            shutil.rmtree(directory)
        except Exception:
            # Best-effort cleanup
            pass


class ProcessMonitor:
    """Monitor process resource usage during execution."""

    def __init__(self):
        self.peak_memory_mb = 0
        self.peak_cpu_percent = 0
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None

    def start_monitoring(self, pid: int):
        """Start monitoring a process."""
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_process, args=(pid,)
        )
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)

    def get_stats(self) -> dict:
        """Get monitoring statistics."""
        return {
            "peak_memory_mb": self.peak_memory_mb,
            "peak_cpu_percent": self.peak_cpu_percent,
        }

    def _monitor_process(self, pid: int):
        """Monitor process resource usage."""
        try:
            import psutil

            process = psutil.Process(pid)

            while self.monitoring:
                try:
                    # Get memory usage
                    memory_info = process.memory_info()
                    memory_mb = memory_info.rss / (1024 * 1024)
                    self.peak_memory_mb = max(self.peak_memory_mb, memory_mb)

                    # Get CPU usage
                    cpu_percent = process.cpu_percent()
                    self.peak_cpu_percent = max(self.peak_cpu_percent, cpu_percent)

                except psutil.NoSuchProcess:
                    break
                except Exception:
                    pass

                time.sleep(0.1)  # Check every 100ms

        except ImportError:
            # psutil not available - monitoring disabled
            pass
        except Exception:
            # Monitoring failed - continue without it
            pass
