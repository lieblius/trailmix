"""Granola API client."""

import gzip
import json
from pathlib import Path
from urllib.request import Request, urlopen

CREDENTIALS_PATH = Path.home() / "Library/Application Support/Granola/supabase.json"
API_BASE = "https://api.granola.ai"


class GranolaClient:
    def __init__(self):
        self.token = self._load_token()

    def _load_token(self) -> str:
        if not CREDENTIALS_PATH.exists():
            raise FileNotFoundError(
                f"Granola credentials not found at {CREDENTIALS_PATH}\n"
                "Make sure Granola is installed and you're logged in."
            )

        with open(CREDENTIALS_PATH) as f:
            creds = json.load(f)

        workos_tokens = json.loads(creds["workos_tokens"])
        token = workos_tokens.get("access_token")

        if not token:
            raise ValueError("No access token found in Granola credentials")

        return token

    def _request(self, endpoint: str, data: dict | None = None) -> dict | list:
        url = f"{API_BASE}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip",
        }

        body = json.dumps(data).encode("utf-8") if data else None
        req = Request(url, data=body, headers=headers, method="POST")

        response = urlopen(req)
        raw = response.read()

        if response.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)

        return json.loads(raw.decode("utf-8"))

    def get_documents(self, include_panels: bool = True) -> list[dict]:
        """Fetch all documents from Granola."""
        all_docs = []
        offset = 0
        limit = 100

        while True:
            result = self._request(
                "/v2/get-documents",
                {
                    "limit": limit,
                    "offset": offset,
                    "include_last_viewed_panel": include_panels,
                },
            )

            if not isinstance(result, dict):
                break

            docs = result.get("docs", [])
            if not docs:
                break

            all_docs.extend(docs)
            offset += limit

            if len(docs) < limit:
                break

        return all_docs

    def get_transcript(self, document_id: str) -> list[dict]:
        """Fetch transcript for a document."""
        try:
            result = self._request(
                "/v1/get-document-transcript",
                {"document_id": document_id},
            )
            if isinstance(result, list):
                return result
            return []
        except Exception:
            return []
