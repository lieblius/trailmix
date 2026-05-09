# Trailmix

CLI tool to sync Granola meeting notes/transcripts to a git repo.

## Commands

```bash
just check      # Run lint, types, tests
just lint       # Ruff linter only
just fix        # Auto-fix lint issues and format
just test       # Pytest only
just types      # ty type checker only
just integration # Full init + sync dry-run against live API
```

## Code Style

- Ruff for linting and formatting (line-length 88)
- Type hints required, checked with `ty`
- Dependencies: `tomli-w`, `cryptography` (for Granola credential decryption)

## Architecture

```
src/trailmix/
  config.py   # Global config at ~/.config/trailmix/config.toml
  granola.py  # Granola API client (auth, get_documents, get_transcript)
  sync.py     # Sync logic, ProseMirror-to-markdown, manifest tracking
  git.py      # Git operations (init, stage, commit)
  cli.py      # CLI commands (init, sync, status, config)
```

## Granola API Notes

- Auth: decrypts `supabase.json.enc` via Chromium OSCrypt (Keychain -> DEK -> AES-256-GCM)
- Falls back to plain-text `supabase.json` if no encrypted file exists
- Granola switched to encrypted storage (`encrypted_supabase_storage` flag) around May 2026
- API returns HTTP 200 with `{"message": "Unsupported client"}` on bad auth (not 401)
- `/v1/get-documents-delta` is deprecated - fetch all docs and diff locally using manifest
- Calendar event `start` field can be string OR dict with `dateTime` key
- Transcript `source`: `microphone` = user (Me), `system` = meeting audio (Them)
- Audio files are NOT retained - only transcripts available

## Development

Install as a tool for testing:
```bash
uv tool install /path/to/trailmix
```

After source changes, must clear cache:
```bash
uv cache clean trailmix && uv tool install --no-cache /path/to/trailmix
```

## Output Structure

```
<meetings_dir>/
  notes/<date>/        # AI notes only
  transcripts/<date>/  # Transcripts only
  combined/<date>/     # Both
  .trailmix/manifest.json  # Sync state (doc IDs, updated_at timestamps)
```
