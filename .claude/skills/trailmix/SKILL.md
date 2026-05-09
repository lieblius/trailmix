---
name: trailmix
description: Read Granola meeting transcripts synced by trailmix. Use when the user mentions trailmix, wants to read meeting transcripts, or asks about past meetings.
allowed-tools: Bash(trailmix *), Bash(ls *), Read(**), Glob(**), Grep(**)
---

# Trailmix - Meeting Transcript Reader

You help users find and read meeting transcripts synced by trailmix from Granola.

## Step 1: Locate meetings directory

Run `trailmix config` to get the meetings directory path. If trailmix is not configured, tell the user to run `trailmix init` first.

## Step 2: Check sync status and sync if needed

Run `trailmix status` to check for new or updated meetings. If there are updates available, run `trailmix sync` to pull them down.

## Step 3: Find and read transcripts

The meetings directory structure is:

```
<meetings_dir>/
  transcripts/<date>/   # Transcript-only files
  combined/<date>/      # Notes + transcripts together
  notes/<date>/         # AI notes only
```

Each file is a markdown file with YAML frontmatter containing `id`, `title`, `date`, and `attendees`.

To find transcripts:
- List date folders with `ls`
- Use Glob to search by pattern: `<meetings_dir>/transcripts/**/*.md`
- Search by attendee or topic with Grep, then read the matched files

## Step 4: Read transcripts FULLY

CRITICAL: Always read the entire transcript file using the Read tool. Never use Grep to partially read a transcript -- transcripts must be read in full to preserve conversational context. If the user asks about a meeting, read the complete file, then summarize or answer questions based on the full content.

If the user wants both notes and transcript together, read from `combined/` instead of `transcripts/`.

## Tips

- If the user says "recent meetings", list the most recent date folders and their contents
- If the user names a person, search frontmatter `attendees` fields with Grep to find files, then Read them fully
- If the user gives a topic, search transcript content with Grep to find relevant files, then Read the full file
- Dates are in `YYYY-MM-DD` format
