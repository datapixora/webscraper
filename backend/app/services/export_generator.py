from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.export import Export, ExportStatus
from app.models.job import Job
from app.models.project import Project
from app.models.result import Result

logger = logging.getLogger(__name__)


class ExportGenerator:
    """
    Synchronous (async-friendly) export generator.
    Generates JSONL/CSV files from Results filtered by project/topic.
    """

    def __init__(self, base_path: Path | None = None) -> None:
        self.base_path = base_path or Path(settings.storage_local_path).resolve() / "exports"

    async def _load_context(
        self, db: AsyncSession, export: Export
    ) -> tuple[Project | None, list[Result]]:
        project = await db.get(Project, export.project_id)
        if not project:
            return None, []

        stmt = (
            select(Result)
            .join(Job, Job.id == Result.job_id)
            .where(Job.project_id == export.project_id)
        )
        if export.topic_id:
            stmt = stmt.where(Job.topic_id == export.topic_id)
        stmt = stmt.order_by(Result.created_at.desc())
        results = list((await db.execute(stmt)).scalars().all())
        return project, results

    def _write_jsonl(self, rows: Iterable[dict], dest: Path) -> int:
        dest.parent.mkdir(parents=True, exist_ok=True)
        count = 0
        with dest.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False))
                f.write("\n")
                count += 1
        return count

    def _write_csv(self, rows: list[dict], dest: Path) -> int:
        dest.parent.mkdir(parents=True, exist_ok=True)
        headers: set[str] = set()
        for row in rows:
            headers.update(row.keys())
        header_list = sorted(headers)
        with dest.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=header_list)
            writer.writeheader()
            writer.writerows(rows)
        return len(rows)

    async def generate(self, db: AsyncSession, export: Export) -> Export:
        project, results = await self._load_context(db, export)
        if not project:
            export.status = ExportStatus.FAILED
            export.error_message = "Project not found"
            await db.commit()
            await db.refresh(export)
            return export

        rows: list[dict] = []
        for res in results:
            row = res.structured_data or {}
            if not row:
                row = {"raw_html": res.raw_html or ""}
            row.setdefault("job_id", res.job_id)
            row.setdefault("project_id", res.project_id)
            row.setdefault("created_at", res.created_at.isoformat() if res.created_at else None)
            rows.append(row)

        if not rows:
            export.status = ExportStatus.FAILED
            export.error_message = "No results available for export"
            await db.commit()
            await db.refresh(export)
            return export

        export_dir = self.base_path / export.project_id / export.id
        export_dir.mkdir(parents=True, exist_ok=True)

        # Decide which file formats to generate
        base_formats = []
        if export.format in {"jsonl", "csv"}:
            base_formats = [export.format]
        elif export.format == "zip":
            base_formats = [fmt for fmt in (project.output_formats or ["jsonl"]) if fmt in {"jsonl", "csv"}]
            if not base_formats:
                base_formats = ["jsonl"]
        else:
            base_formats = ["jsonl"]

        generated_files: list[Path] = []
        total_count = 0

        try:
            for fmt in base_formats:
                file_path = export_dir / f"{export.name}.{fmt}"
                if fmt == "jsonl":
                    count = self._write_jsonl(rows, file_path)
                else:
                    count = self._write_csv(rows, file_path)
                generated_files.append(file_path)
                total_count = max(total_count, count)

            file_path: Path
            if project.compression_enabled or export.format == "zip":
                zip_path = export_dir / f"{export.name}.zip"
                import zipfile

                with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                    for path in generated_files:
                        zf.write(path, arcname=path.name)
                file_path = zip_path
                export.format = "zip"
            else:
                file_path = generated_files[0]

            size = file_path.stat().st_size
            export.file_path = str(file_path)
            export.file_size = size
            export.record_count = total_count
            export.status = ExportStatus.READY
            export.error_message = None
            await db.commit()
            await db.refresh(export)
            return export
        except Exception as exc:  # noqa: BLE001
            logger.exception("export_generation_failed", extra={"export_id": export.id})
            export.status = ExportStatus.FAILED
            export.error_message = str(exc)
            await db.commit()
            await db.refresh(export)
            return export


export_generator = ExportGenerator()

__all__ = ["export_generator", "ExportGenerator"]
