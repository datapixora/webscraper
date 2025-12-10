from __future__ import annotations

import gzip
import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol, TypedDict

import boto3

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageSaveResult(TypedDict):
    path: str
    checksum: str
    size_bytes: int
    compressed_size_bytes: int


class StorageBackend(Protocol):
    def save_raw_html(self, project_id: str, job_id: str, html: str) -> StorageSaveResult:
        """Persist raw HTML and return metadata."""

    def fetch_raw_html(self, path: str) -> str:
        """Retrieve raw HTML (decompressed)."""


@dataclass
class LocalStorageBackend:
    base_path: Path

    def save_raw_html(self, project_id: str, job_id: str, html: str) -> StorageSaveResult:
        relative_key = Path("project") / project_id / "job" / job_id / "raw.html.gz"
        full_path = self.base_path / relative_key
        full_path.parent.mkdir(parents=True, exist_ok=True)

        data = html.encode("utf-8", errors="ignore")
        compressed = gzip.compress(data)
        checksum = hashlib.sha256(compressed).hexdigest()

        with full_path.open("wb") as f:
            f.write(compressed)

        logger.info("Saved raw HTML locally", extra={"path": str(full_path), "size": len(data)})
        return {
            "path": str(full_path),
            "checksum": checksum,
            "size_bytes": len(data),
            "compressed_size_bytes": len(compressed),
        }

    def fetch_raw_html(self, path: str) -> str:
        full_path = Path(path)
        if not full_path.is_absolute():
            full_path = self.base_path / path
        compressed = full_path.read_bytes()
        return gzip.decompress(compressed).decode("utf-8", errors="ignore")


@dataclass
class S3StorageBackend:
    bucket: str
    region: Optional[str] = None
    endpoint_url: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None

    def _client(self):
        return boto3.client(
            "s3",
            region_name=self.region,
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

    def save_raw_html(self, project_id: str, job_id: str, html: str) -> StorageSaveResult:
        key = f"project/{project_id}/job/{job_id}/raw.html.gz"
        data = html.encode("utf-8", errors="ignore")
        compressed = gzip.compress(data)
        checksum = hashlib.sha256(compressed).hexdigest()

        client = self._client()
        client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=compressed,
            ContentType="application/gzip",
            ContentEncoding="gzip",
            Metadata={
                "original-size": str(len(data)),
                "checksum": checksum,
            },
        )

        path = f"s3://{self.bucket}/{key}"
        logger.info("Saved raw HTML to S3", extra={"path": path, "size": len(data)})
        return {
            "path": path,
            "checksum": checksum,
            "size_bytes": len(data),
            "compressed_size_bytes": len(compressed),
        }

    def fetch_raw_html(self, path: str) -> str:
        if not path.startswith("s3://"):
            raise ValueError("S3 backend requires an s3:// path")
        prefix = f"s3://{self.bucket}/"
        key = path[len(prefix) :] if path.startswith(prefix) else path
        client = self._client()
        obj = client.get_object(Bucket=self.bucket, Key=key)
        compressed = obj["Body"].read()
        return gzip.decompress(compressed).decode("utf-8", errors="ignore")


class StorageService:
    def __init__(self, backend: StorageBackend):
        self.backend = backend

    @classmethod
    def from_settings(cls, cfg=settings) -> "StorageService":
        backend_name = (cfg.storage_backend or "local").lower()
        if backend_name == "s3":
            backend = S3StorageBackend(
                bucket=cfg.aws_s3_bucket,
                region=cfg.aws_s3_region,
                endpoint_url=cfg.aws_s3_endpoint_url,
                access_key=cfg.aws_access_key_id,
                secret_key=cfg.aws_secret_access_key,
            )
        else:
            base_path = Path(cfg.storage_local_path).resolve()
            backend = LocalStorageBackend(base_path=base_path)
        return cls(backend=backend)

    def save_raw_html(self, project_id: str, job_id: str, html: str) -> StorageSaveResult:
        return self.backend.save_raw_html(project_id, job_id, html)

    def fetch_raw_html(self, path: str) -> str:
        return self.backend.fetch_raw_html(path)


storage_service = StorageService.from_settings()

__all__ = ["storage_service", "StorageService", "StorageBackend", "StorageSaveResult"]
