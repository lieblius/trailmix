"""Tests for sync module."""

from trailmix.sync import (
    prosemirror_to_markdown,
    sanitize_filename,
    format_transcript,
)


def test_sanitize_filename():
    assert sanitize_filename("Hello World") == "Hello_World"
    assert sanitize_filename("Test/File:Name") == "TestFileName"
    assert sanitize_filename("A" * 100) == "A" * 80
    assert sanitize_filename("") == "untitled"


def test_prosemirror_heading():
    content = {
        "type": "doc",
        "content": [
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{"type": "text", "text": "Hello"}],
            }
        ],
    }
    result = prosemirror_to_markdown(content)
    assert result == "## Hello"


def test_prosemirror_paragraph():
    content = {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": "Hello world"}],
            }
        ],
    }
    result = prosemirror_to_markdown(content)
    assert result == "Hello world"


def test_prosemirror_bullet_list():
    content = {
        "type": "doc",
        "content": [
            {
                "type": "bulletList",
                "content": [
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": "Item 1"}],
                            }
                        ],
                    },
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": "Item 2"}],
                            }
                        ],
                    },
                ],
            }
        ],
    }
    result = prosemirror_to_markdown(content)
    assert "- Item 1" in result
    assert "- Item 2" in result


def test_prosemirror_empty():
    assert prosemirror_to_markdown(None) == ""
    assert prosemirror_to_markdown({}) == ""


def test_format_transcript():
    entries = [
        {
            "start_timestamp": "2026-01-21T16:39:37.784Z",
            "text": "Hello there",
        },
        {
            "start_timestamp": "2026-01-21T16:39:45.000Z",
            "text": "How are you",
        },
    ]
    result = format_transcript(entries)
    assert "[16:39:37] Hello there" in result
    assert "[16:39:45] How are you" in result


def test_format_transcript_empty():
    assert format_transcript([]) == ""
    assert format_transcript(None) == ""
