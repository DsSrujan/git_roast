import os
import subprocess
import tempfile
import sys
import shutil
import stat

def _remove_readonly(func, path, excinfo):
    """Clear the read-only attribute on Windows so files can be deleted."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass

class GitAnalyzer:
    def __init__(self, repo_url: str):
        self.repo_url = repo_url.strip()

    def fetch_and_parse(self, limit: int = 15):
        tmpdir = tempfile.mkdtemp()
        try:
            subprocess.run(
                ["git", "clone", "--depth", "10", "--single-branch", self.repo_url, tmpdir],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="ignore",
                check=True,
                timeout=20
            )

            log_output = subprocess.run(
                ["git", "-C", tmpdir, "log", f"-n{limit}", "--pretty=format:%h|%an|%s"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="ignore",
                check=True
            ).stdout.strip()

            if not log_output:
                return []

            commits = []
            for line in log_output.split("\n"):
                if not line:
                    continue
                parts = line.split("|", 2)
                if len(parts) == 3:
                    h, author, msg = parts
                    
                    stat_output = subprocess.run(
                        ["git", "-C", tmpdir, "show", "--shortstat", h],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        encoding="utf-8",
                        errors="ignore"
                    ).stdout.strip()
                    
                    stat_summary = stat_output.split("\n")[-1].strip() if stat_output else "No stats"
                    commits.append({
                        "hash": h,
                        "author": author,
                        "message": msg,
                        "stats": stat_summary
                    })

            return commits
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git clone failed: {e.stderr.strip()}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Git clone timed out.")
        finally:
            if os.path.exists(tmpdir):
                shutil.rmtree(tmpdir, onerror=_remove_readonly)

