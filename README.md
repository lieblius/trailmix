# trailmix

Sync Granola meeting notes to a git repo.

## Prerequisites

- macOS
- [Granola](https://granola.ai) installed and signed in
- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

## Install

```bash
uv tool install /path/to/trailmix
```

To update after changes:

```bash
uv tool install --force /path/to/trailmix
```

## Usage

Initialize trailmix (creates meetings directory and saves config):

```bash
trailmix init ~/meetings
```

Or initialize in current directory:

```bash
cd ~/meetings
trailmix init
```

Sync your Granola meetings (works from any directory):

```bash
trailmix sync
```

Preview what would be synced without making changes:

```bash
trailmix sync --dry-run
```

Check sync status:

```bash
trailmix status
```

Show current configuration:

```bash
trailmix config
```

## Configuration

Config is stored at `~/.config/trailmix/config.toml`:

```toml
meetings_dir = "/Users/you/meetings"
```

Granola credentials are read automatically from `~/Library/Application Support/Granola/supabase.json` (created when you sign into Granola).

## Structure

```
meetings/
  notes/
    2026-01-21/
      Meeting_Title.md     # AI-generated notes only
  transcripts/
    2026-01-21/
      Meeting_Title.md     # transcript only
  combined/
    2026-01-21/
      Meeting_Title.md     # notes + transcript
  .trailmix/
    manifest.json          # sync state
```
