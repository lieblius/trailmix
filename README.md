# trailmix

Sync Granola meeting notes to a git repo.

## Install

```bash
uv tool install /path/to/trailmix
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

Check what would be synced:

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
