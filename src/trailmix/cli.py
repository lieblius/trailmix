"""CLI for trailmix."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .git import commit, has_changes, init_repo, is_git_repo
from .sync import TRAILMIX_DIR, find_repo_root, load_manifest, sync


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize a new trailmix repo."""
    path = Path(args.path or ".").resolve()

    if not path.exists():
        path.mkdir(parents=True)

    trailmix_dir = path / TRAILMIX_DIR
    notes_dir = path / "notes"
    transcripts_dir = path / "transcripts"
    combined_dir = path / "combined"

    if trailmix_dir.exists():
        print(f"Already initialized: {path}")
        return 1

    trailmix_dir.mkdir()
    notes_dir.mkdir()
    transcripts_dir.mkdir()
    combined_dir.mkdir()

    if not is_git_repo(path):
        init_repo(path)
        print(f"Initialized git repo: {path}")

    gitignore = path / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("# Add patterns to ignore\n")

    print(f"Initialized trailmix repo: {path}")
    print("  notes/       - AI-generated notes only")
    print("  transcripts/ - transcripts only")
    print("  combined/    - notes + transcripts")
    print(f"  {TRAILMIX_DIR}/       - sync state")
    print()
    print("Run 'trailmix sync' to sync your Granola meetings.")

    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    """Sync Granola meetings to the repo."""
    repo_root = find_repo_root()

    if not repo_root:
        print("Not in a trailmix repo. Run 'trailmix init' first.")
        return 1

    dry_run = args.dry_run

    if dry_run:
        print("Dry run - no changes will be made\n")

    try:
        result = sync(repo_root, dry_run=dry_run)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Sync failed: {e}")
        return 1

    if result.new:
        print(f"New ({len(result.new)}):")
        for title in result.new:
            print(f"  + {title}")

    if result.updated:
        print(f"Updated ({len(result.updated)}):")
        for title in result.updated:
            print(f"  ~ {title}")

    if not result.new and not result.updated:
        print("Already up to date.")
        return 0

    if dry_run:
        print(f"\nWould sync {len(result.new)} new, {len(result.updated)} updated")
        return 0

    total = len(result.new) + len(result.updated)
    msg_parts = []
    if result.new:
        msg_parts.append(f"{len(result.new)} new")
    if result.updated:
        msg_parts.append(f"{len(result.updated)} updated")

    commit_msg = f"sync: {', '.join(msg_parts)} meeting{'s' if total != 1 else ''}"

    commit_hash = commit(repo_root, commit_msg)

    if commit_hash:
        print(f"\nCommitted: {commit_hash} - {commit_msg}")
    else:
        print("\nNo changes to commit.")

    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Show sync status."""
    repo_root = find_repo_root()

    if not repo_root:
        print("Not in a trailmix repo. Run 'trailmix init' first.")
        return 1

    manifest = load_manifest(repo_root)
    docs = manifest.get("documents", {})

    print(f"Trailmix repo: {repo_root}")
    print(f"Synced meetings: {len(docs)}")

    if has_changes(repo_root):
        print("Git status: uncommitted changes")
    else:
        print("Git status: clean")

    print("\nChecking for updates...")

    try:
        result = sync(repo_root, dry_run=True)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error checking status: {e}")
        return 1

    if result.new:
        print(f"\nNew meetings to sync ({len(result.new)}):")
        for title in result.new:
            print(f"  + {title}")

    if result.updated:
        print(f"\nUpdated meetings to sync ({len(result.updated)}):")
        for title in result.updated:
            print(f"  ~ {title}")

    if not result.new and not result.updated:
        print("\nNo new meetings to sync.")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="trailmix",
        description="Sync Granola meeting notes to a git repo",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize a new trailmix repo")
    init_parser.add_argument(
        "path",
        nargs="?",
        help="Directory to initialize (default: current directory)",
    )

    sync_parser = subparsers.add_parser("sync", help="Sync Granola meetings")
    sync_parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show what would be synced without making changes",
    )

    subparsers.add_parser("status", help="Show sync status")

    args = parser.parse_args()

    if args.command == "init":
        return cmd_init(args)
    elif args.command == "sync":
        return cmd_sync(args)
    elif args.command == "status":
        return cmd_status(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
