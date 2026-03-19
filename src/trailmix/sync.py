"""Sync logic for Granola meetings."""

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .granola import GranolaClient

TRAILMIX_DIR = ".trailmix"
MANIFEST_FILE = "manifest.json"


@dataclass
class SyncResult:
    new: list[str]
    updated: list[str]
    skipped: int


def load_manifest(repo_root: Path) -> dict:
    """Load the sync manifest."""
    manifest_path = repo_root / TRAILMIX_DIR / MANIFEST_FILE

    if not manifest_path.exists():
        return {"documents": {}}

    with open(manifest_path) as f:
        return json.load(f)


def save_manifest(repo_root: Path, manifest: dict) -> None:
    """Save the sync manifest."""
    manifest_path = repo_root / TRAILMIX_DIR / MANIFEST_FILE

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)


def prosemirror_to_markdown(content: dict) -> str:
    """Convert ProseMirror JSON to Markdown."""
    if not content or not isinstance(content, dict):
        return ""

    def process_node(node: dict) -> str:
        if not isinstance(node, dict):
            return ""

        node_type = node.get("type", "")
        children = node.get("content", [])
        text = node.get("text", "")

        if node_type == "doc":
            return "".join(process_node(child) for child in children)

        if node_type == "heading":
            level = node.get("attrs", {}).get("level", 1)
            heading_text = "".join(process_node(child) for child in children)
            return f"{'#' * level} {heading_text}\n\n"

        if node_type == "paragraph":
            para_text = "".join(process_node(child) for child in children)
            return f"{para_text}\n\n"

        if node_type == "bulletList":
            items = []
            for item in children:
                if item.get("type") == "listItem":
                    item_content = "".join(
                        process_node(child) for child in item.get("content", [])
                    )
                    items.append(f"- {item_content.strip()}")
            return "\n".join(items) + "\n\n"

        if node_type == "orderedList":
            items = []
            for i, item in enumerate(children, 1):
                if item.get("type") == "listItem":
                    item_content = "".join(
                        process_node(child) for child in item.get("content", [])
                    )
                    items.append(f"{i}. {item_content.strip()}")
            return "\n".join(items) + "\n\n"

        if node_type == "listItem":
            return "".join(process_node(child) for child in children)

        if node_type == "text":
            result = text
            marks = node.get("marks", [])
            for mark in marks:
                mark_type = mark.get("type")
                if mark_type == "bold":
                    result = f"**{result}**"
                elif mark_type == "italic":
                    result = f"*{result}*"
                elif mark_type == "code":
                    result = f"`{result}`"
                elif mark_type == "link":
                    href = mark.get("attrs", {}).get("href", "")
                    result = f"[{result}]({href})"
            return result

        if node_type == "codeBlock":
            code_text = "".join(process_node(child) for child in children)
            lang = node.get("attrs", {}).get("language", "")
            return f"```{lang}\n{code_text}\n```\n\n"

        if node_type == "blockquote":
            quote_text = "".join(process_node(child) for child in children)
            lines = quote_text.strip().split("\n")
            return "\n".join(f"> {line}" for line in lines) + "\n\n"

        if node_type == "horizontalRule":
            return "---\n\n"

        return "".join(process_node(child) for child in children)

    return process_node(content).strip()


def format_transcript(entries: list[dict]) -> str:
    """Format transcript entries into markdown."""
    if not entries:
        return ""

    lines = []
    for entry in sorted(entries, key=lambda x: x.get("start_timestamp", "")):
        ts = entry.get("start_timestamp", "")
        text = entry.get("text", "").strip()
        source = entry.get("source", "")

        if ts and text:
            speaker = "Me" if source == "microphone" else "Them"
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                time_str = dt.strftime("%H:%M:%S")
                lines.append(f"[{time_str}] **{speaker}:** {text}")
            except ValueError:
                lines.append(f"**{speaker}:** {text}")

    return "\n\n".join(lines)


def sanitize_filename(title: str) -> str:
    """Convert title to a safe filename."""
    filename = re.sub(r'[<>:"/\\|?*]', "", title)
    filename = re.sub(r"\s+", "_", filename)
    filename = filename[:80]
    return filename or "untitled"


def get_document_date(doc: dict) -> str:
    """Extract date from document."""
    event = doc.get("google_calendar_event")
    if event and event.get("start"):
        start = event["start"]
        # Granola API returns start as either a dict with dateTime key or a string
        if isinstance(start, dict):
            start = start.get("dateTime", "")
        if start:
            try:
                dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

    created_at = doc.get("created_at", "")
    if created_at:
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    return "unknown-date"


def get_attendees(doc: dict) -> list[str]:
    """Extract attendees from document."""
    event = doc.get("google_calendar_event")
    if not event:
        return []

    attendees = event.get("attendees", [])
    names = []
    for a in attendees:
        name = a.get("displayName") or a.get("email", "").split("@")[0]
        if name:
            names.append(name)

    return names


def build_frontmatter(doc: dict) -> str:
    """Build YAML frontmatter for a document."""
    doc_id = doc.get("id", "")
    title = doc.get("title", "Untitled").replace('"', "'")
    date = get_document_date(doc)
    attendees = get_attendees(doc)

    lines = ["---"]
    lines.append(f"id: {doc_id}")
    lines.append(f'title: "{title}"')
    lines.append(f"date: {date}")

    if attendees:
        lines.append("attendees:")
        for a in attendees:
            lines.append(f'  - "{a}"')

    lines.append("---")
    return "\n".join(lines)


def write_note_file(repo_root: Path, doc: dict) -> Path:
    """Write a notes-only file."""
    date_str = get_document_date(doc)
    title = doc.get("title", "Untitled")
    filename = sanitize_filename(title) + ".md"

    date_dir = repo_root / "notes" / date_str
    date_dir.mkdir(parents=True, exist_ok=True)
    filepath = date_dir / filename

    parts = []
    parts.append(build_frontmatter(doc))
    parts.append("")
    parts.append(f"# {title}")
    parts.append("")

    panel = doc.get("last_viewed_panel")
    if panel and panel.get("content"):
        notes_md = prosemirror_to_markdown(panel["content"])
        if notes_md:
            parts.append(notes_md)
            parts.append("")

    content = "\n".join(parts)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def write_transcript_file(repo_root: Path, doc: dict, transcript: list[dict]) -> Path:
    """Write a transcript-only file."""
    date_str = get_document_date(doc)
    title = doc.get("title", "Untitled")
    filename = sanitize_filename(title) + ".md"

    date_dir = repo_root / "transcripts" / date_str
    date_dir.mkdir(parents=True, exist_ok=True)
    filepath = date_dir / filename

    parts = []
    parts.append(build_frontmatter(doc))
    parts.append("")
    parts.append(f"# {title}")
    parts.append("")

    if transcript:
        transcript_md = format_transcript(transcript)
        if transcript_md:
            parts.append(transcript_md)
            parts.append("")

    content = "\n".join(parts)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def write_combined_file(repo_root: Path, doc: dict, transcript: list[dict]) -> Path:
    """Write a combined notes + transcript file."""
    date_str = get_document_date(doc)
    title = doc.get("title", "Untitled")
    filename = sanitize_filename(title) + ".md"

    date_dir = repo_root / "combined" / date_str
    date_dir.mkdir(parents=True, exist_ok=True)
    filepath = date_dir / filename

    parts = []
    parts.append(build_frontmatter(doc))
    parts.append("")
    parts.append(f"# {title}")
    parts.append("")

    panel = doc.get("last_viewed_panel")
    if panel and panel.get("content"):
        notes_md = prosemirror_to_markdown(panel["content"])
        if notes_md:
            parts.append(notes_md)
            parts.append("")

    if transcript:
        transcript_md = format_transcript(transcript)
        if transcript_md:
            parts.append("## Transcript")
            parts.append("")
            parts.append(transcript_md)
            parts.append("")

    content = "\n".join(parts)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def needs_sync(doc: dict, manifest: dict) -> bool:
    """Check if a document needs to be synced."""
    doc_id = doc.get("id")
    updated_at = doc.get("updated_at")

    if not doc_id:
        return False

    if doc.get("deleted_at"):
        return False

    doc_manifest = manifest.get("documents", {}).get(doc_id)

    if not doc_manifest:
        return True

    last_synced = doc_manifest.get("updated_at")
    return bool(updated_at and last_synced and updated_at > last_synced)


def sync(repo_root: Path, dry_run: bool = False) -> SyncResult:
    """Sync all Granola documents to the repo."""
    client = GranolaClient()
    manifest = load_manifest(repo_root)

    documents = client.get_documents()

    new_docs = []
    updated_docs = []
    skipped = 0

    for doc in documents:
        doc_id = doc.get("id")
        title = doc.get("title")

        if not title:
            print(f"  Skipping untitled meeting ({doc_id}) - name it in Granola first")
            skipped += 1
            continue

        if not doc_id or not needs_sync(doc, manifest):
            skipped += 1
            continue

        is_new = doc_id not in manifest.get("documents", {})

        if dry_run:
            if is_new:
                new_docs.append(title)
            else:
                updated_docs.append(title)
            continue

        transcript = client.get_transcript(doc_id)

        write_note_file(repo_root, doc)
        write_transcript_file(repo_root, doc, transcript)
        write_combined_file(repo_root, doc, transcript)

        if "documents" not in manifest:
            manifest["documents"] = {}

        manifest["documents"][doc_id] = {
            "title": title,
            "updated_at": doc.get("updated_at"),
            "synced_at": datetime.now(UTC).isoformat(),
        }

        if is_new:
            new_docs.append(title)
        else:
            updated_docs.append(title)

    if not dry_run:
        save_manifest(repo_root, manifest)

    return SyncResult(new=new_docs, updated=updated_docs, skipped=skipped)
