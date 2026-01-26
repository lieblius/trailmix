"""Git integration for trailmix."""

import subprocess
from pathlib import Path


class GitError(Exception):
    """Git command failed."""

    pass


def run_git(repo_root: Path, *args: str) -> str:
    """Run a git command in the repo."""
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {result.stderr}")

    return result.stdout


def is_git_repo(path: Path) -> bool:
    """Check if path is inside a git repo."""
    try:
        run_git(path, "rev-parse", "--git-dir")
        return True
    except GitError:
        return False


def init_repo(path: Path) -> None:
    """Initialize a git repo if not already one."""
    if not is_git_repo(path):
        run_git(path, "init")


def has_changes(repo_root: Path) -> bool:
    """Check if there are uncommitted changes."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())


def stage_all(repo_root: Path) -> None:
    """Stage all changes."""
    run_git(repo_root, "add", "-A")


def commit(repo_root: Path, message: str) -> str | None:
    """Commit staged changes. Returns commit hash or None if nothing to commit."""
    if not has_changes(repo_root):
        return None

    stage_all(repo_root)

    staged_check = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=repo_root,
    )

    if staged_check.returncode == 0:
        return None

    run_git(repo_root, "commit", "-m", message)

    return run_git(repo_root, "rev-parse", "--short", "HEAD").strip()
