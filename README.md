# trailmix

Sync Granola meeting notes to a git repo.

## Install

```bash
uv tool install /path/to/trailmix
```

## Usage

Initialize a new meetings repo:

```bash
mkdir ~/meetings && cd ~/meetings
trailmix init
```

Sync your Granola meetings:

```bash
trailmix sync
```

Check what would be synced:

```bash
trailmix status
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
