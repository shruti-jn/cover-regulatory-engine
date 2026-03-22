"""
Assessment export service.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from uuid import UUID

import structlog
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.export import ExportResponse
from src.services.assessments import get_assessment_service

logger = structlog.get_logger()


class AssessmentExportService:
    """Generate portable assessment exports."""

    def __init__(self, export_root: Path | None = None):
        self.export_root = export_root or Path("artifacts/exports")

    async def export_assessment(self, *, db: AsyncSession, assessment_id: UUID) -> ExportResponse:
        assessment_service = get_assessment_service()
        assessment = await assessment_service._load_assessment_with_relationships(db, assessment_id)
        response = await assessment_service._serialize_assessment(db, assessment)

        export_dir = self.export_root / str(assessment_id)
        export_dir.mkdir(parents=True, exist_ok=True)
        export_path = export_dir / "assessment_export.pdf"
        self._write_pdf(export_path, response)

        unresolved_items = self._collect_unresolved_items(response)
        logger.info(
            "assessment_export_generated",
            assessment_id=str(assessment_id),
            export_path=str(export_path),
            unresolved_count=len(unresolved_items),
        )
        return ExportResponse(
            download_url=str(export_path.resolve()),
            format="pdf",
            included_fields=["constraints", "evidence", "geometry", "scenario_diff"],
            unresolved_items=unresolved_items,
        )

    def _write_pdf(self, export_path: Path, response) -> None:
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        y = 750

        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(72, y, "Cover Assessment Export")
        y -= 28

        pdf.setFont("Helvetica", 11)
        pdf.drawString(72, y, f"Assessment ID: {response.assessment_id}")
        y -= 20
        pdf.drawString(72, y, f"Geometry Type: {response.parcel_geometry.type}")
        y -= 24

        for index, constraint in enumerate(response.constraints, start=1):
            pdf.setFont("Helvetica-Bold", 11)
            pdf.drawString(72, y, f"Constraint {index}: {constraint.domain}")
            y -= 16
            pdf.setFont("Helvetica", 10)
            pdf.drawString(72, y, f"Value: {constraint.constraint_value.type}={constraint.constraint_value.value}")
            y -= 14
            pdf.drawString(72, y, f"Provenance: {constraint.provenance_state}")
            y -= 14
            pdf.drawString(72, y, f"Confidence: {constraint.confidence_score:.2f}")
            y -= 14
            for evidence in constraint.evidence:
                line = (
                    f"Evidence: {evidence.source_title} | {evidence.jurisdiction} | "
                    f"page={evidence.page_number}"
                )
                pdf.drawString(84, y, line[:100])
                y -= 12
            y -= 10
            if y < 100:
                pdf.showPage()
                y = 750

        pdf.save()
        export_path.write_bytes(buffer.getvalue())

    def _collect_unresolved_items(self, response) -> list[str]:
        unresolved_items = []
        for constraint in response.constraints:
            if constraint.provenance_state != "deterministic":
                unresolved_items.append(
                    f"{constraint.domain}: provenance_state={constraint.provenance_state}"
                )
            if not constraint.evidence:
                unresolved_items.append(f"{constraint.domain}: missing evidence")
        return unresolved_items


_service: AssessmentExportService | None = None


def get_assessment_export_service() -> AssessmentExportService:
    global _service
    if _service is None:
        _service = AssessmentExportService()
    return _service
