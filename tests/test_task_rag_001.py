from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4
import asyncio

from src.models.extracted_rule import RuleDomain, RuleType
from src.models.ingested_document import IngestedDocument
from src.models.ingestion_pipeline import IngestionPipelineStatus
from src.services.embeddings import EmbeddingService
from src.services.ingestion.service import IngestionJobStatus, IngestionService
from src.workers.rag.pipeline import DocumentIngestionWorker


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _FakeSession:
    def __init__(self):
        self.jobs: dict = {}
        self.documents: list[IngestedDocument] = []
        self.rules = []
        self.provenance = []
        self._pending_document_lookup = None

    def add(self, obj):
        if getattr(obj, "id", None) is None:
            obj.id = uuid4()
        if isinstance(obj, IngestionPipelineStatus):
            self.jobs[obj.id] = obj
        elif isinstance(obj, IngestedDocument):
            self.documents.append(obj)
        elif obj.__class__.__name__ == "ExtractedRule":
            self.rules.append(obj)
        elif obj.__class__.__name__ == "RuleProvenance":
            self.provenance.append(obj)

    async def flush(self):
        return None

    async def get(self, model, identifier):
        if model is IngestionPipelineStatus:
            return self.jobs.get(identifier)
        return None

    async def execute(self, stmt):
        return _ScalarResult(self._pending_document_lookup)


def test_ingestion_service_processes_text_and_persists_rules():
    service = IngestionService(EmbeddingService())
    db = _FakeSession()
    job = asyncio.run(
        service.queue_job(
            db=db,
            document_url="https://example.com/adu-guide.txt",
            jurisdiction="LA City",
        )
    )

    summary = asyncio.run(
        service.process_job(
            db=db,
            job_id=job.id,
            document_url="https://example.com/adu-guide.txt",
            jurisdiction="LA City",
            source_bytes=b"Front setback shall be 20 ft. ADU may be allowed in the rear yard.",
            content_type="text/plain",
            title="ADU Guide",
        )
    )

    assert summary.status == IngestionJobStatus.COMPLETED
    assert summary.duplicate_skipped is False
    assert len(db.documents) == 1
    assert db.documents[0].title == "ADU Guide"
    assert db.documents[0].document_metadata["chunk_count"] >= 1
    assert len(db.rules) >= 1
    assert db.rules[0].domain in {RuleDomain.SETBACK, RuleDomain.ADU}
    assert db.rules[0].rule_type in {RuleType.DETERMINISTIC, RuleType.INTERPRETED}
    assert len(db.provenance) == len(db.rules)


def test_ingestion_service_skips_duplicate_checksum():
    service = IngestionService(EmbeddingService())
    db = _FakeSession()
    existing_document = IngestedDocument(
        title="Existing",
        jurisdiction="LA City",
        source_url="https://example.com/code.pdf",
        version_hash="abc123",
        raw_text="Setback shall be 20 ft.",
        document_metadata={},
    )
    db._pending_document_lookup = existing_document
    job = asyncio.run(
        service.queue_job(
            db=db,
            document_url="https://example.com/code.pdf",
            jurisdiction="LA City",
        )
    )

    summary = asyncio.run(
        service.process_job(
            db=db,
            job_id=job.id,
            document_url="https://example.com/code.pdf",
            jurisdiction="LA City",
            source_bytes=b"anything",
            content_type="text/plain",
        )
    )

    assert summary.status == IngestionJobStatus.COMPLETED
    assert summary.duplicate_skipped is True
    assert summary.document_id == existing_document.id
    assert len(db.rules) == 0


def test_worker_runs_job_and_returns_completed_summary():
    service = IngestionService(EmbeddingService())
    worker = DocumentIngestionWorker(service)
    db = _FakeSession()
    job = asyncio.run(
        service.queue_job(
            db=db,
            document_url="https://example.com/height.txt",
            jurisdiction="LA City",
        )
    )

    summary = asyncio.run(
        worker.run_job(
            db=db,
            job_id=job.id,
            document_url="https://example.com/height.txt",
            jurisdiction="LA City",
            source_bytes=b"Maximum height shall be 30 feet.",
            content_type="text/plain",
            title="Height Rules",
        )
    )

    assert summary.status == IngestionJobStatus.COMPLETED
    assert db.jobs[job.id].status == IngestionJobStatus.COMPLETED
