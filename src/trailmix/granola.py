"""Granola API client."""

import gzip
import hashlib
import json
import subprocess
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

GRANOLA_DIR = Path.home() / "Library/Application Support/Granola"
CREDENTIALS_PATH = GRANOLA_DIR / "supabase.json"
ENCRYPTED_CREDENTIALS_PATH = GRANOLA_DIR / "supabase.json.enc"
DEK_PATH = GRANOLA_DIR / "storage.dek"
KEYCHAIN_SERVICE = "Granola Safe Storage"
API_BASE = "https://api.granola.ai"

OSCRYPT_SALT = b"saltysalt"
OSCRYPT_ITERATIONS = 1003
OSCRYPT_KEY_LEN = 16
OSCRYPT_IV = b"\x20" * 16


class GranolaAuthError(Exception):
    pass


def _get_keychain_password() -> str:
    """Retrieve the Granola encryption password from macOS Keychain."""
    try:
        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-w",
                "-s",
                KEYCHAIN_SERVICE,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise GranolaAuthError(
            "Could not read Granola encryption key from "
            "macOS Keychain.\n"
            f"security error: {e.stderr.strip()}"
        ) from None


def _decrypt_dek() -> bytes:
    """Decrypt the Data Encryption Key using the Keychain password.

    Chromium OSCrypt v10 format:
    - "v10" prefix (3 bytes)
    - AES-128-CBC ciphertext with PKCS7 padding
    - Key derived via PBKDF2(keychain_password, "saltysalt", 1003)
    - IV is 16 space characters (0x20)
    """
    password = _get_keychain_password()

    raw = DEK_PATH.read_bytes()
    if not raw.startswith(b"v10"):
        raise GranolaAuthError(
            f"Unexpected DEK format (expected v10 prefix, "
            f"got {raw[:3]!r})"
        )
    ciphertext = raw[3:]

    key = hashlib.pbkdf2_hmac(
        "sha1",
        password.encode("utf-8"),
        OSCRYPT_SALT,
        OSCRYPT_ITERATIONS,
        dklen=OSCRYPT_KEY_LEN,
    )

    cipher = Cipher(algorithms.AES128(key), modes.CBC(OSCRYPT_IV))
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()

    pad_len = padded[-1]
    return padded[:-pad_len]


def _decrypt_credentials() -> dict:
    """Decrypt supabase.json.enc using the DEK.

    Format: 12-byte nonce + ciphertext + 16-byte GCM auth tag.
    DEK is base64-encoded after Chromium OSCrypt decryption.
    """
    import base64

    dek = base64.b64decode(_decrypt_dek())
    raw = ENCRYPTED_CREDENTIALS_PATH.read_bytes()

    nonce = raw[:12]
    ct_and_tag = raw[12:]

    aesgcm = AESGCM(dek)
    plaintext = aesgcm.decrypt(nonce, ct_and_tag, None)

    return json.loads(plaintext.decode("utf-8"))


class GranolaClient:
    def __init__(self):
        self.token = self._load_token()

    def _load_token(self) -> str:
        if ENCRYPTED_CREDENTIALS_PATH.exists() and DEK_PATH.exists():
            creds = _decrypt_credentials()
        elif CREDENTIALS_PATH.exists():
            with open(CREDENTIALS_PATH) as f:
                creds = json.load(f)
        else:
            raise FileNotFoundError(
                "Granola credentials not found at "
                f"{GRANOLA_DIR}\n"
                "Make sure Granola is installed and "
                "you're logged in."
            )

        workos_tokens = json.loads(creds["workos_tokens"])
        token = workos_tokens.get("access_token")

        if not token:
            raise ValueError(
                "No access token found in Granola credentials"
            )

        return token

    def _request(
        self, endpoint: str, data: dict | None = None
    ) -> dict | list:
        url = f"{API_BASE}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip",
        }

        body = json.dumps(data).encode("utf-8") if data else None
        req = Request(url, data=body, headers=headers, method="POST")

        try:
            response = urlopen(req)
        except HTTPError as e:
            if e.code == 401:
                raise GranolaAuthError(
                    "Authentication failed (HTTP 401). "
                    "Your token may be expired."
                ) from None
            raise

        raw = response.read()

        if response.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)

        result = json.loads(raw.decode("utf-8"))

        if (
            isinstance(result, dict)
            and "message" in result
            and "docs" not in result
        ):
            msg = result["message"]
            if "unsupported" in msg.lower():
                raise GranolaAuthError(
                    f"Granola API rejected the request: {msg}\n"
                    "This usually means your token is expired "
                    "or invalid."
                )
            raise RuntimeError(f"Granola API error: {msg}")

        return result

    def get_documents(
        self, include_panels: bool = True
    ) -> list[dict]:
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
