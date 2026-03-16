from __future__ import annotations

import base64

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import DBSession
from app.schemas.api import ReportResponse
from app.services.reports import build_markdown_report, build_pdf_from_markdown

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/investigations/{investigation_id}", response_model=ReportResponse)
def report(
    investigation_id: int,
    db: DBSession,
    format: str = Query(default="markdown", pattern="^(markdown|pdf)$"),
) -> ReportResponse:
    markdown = build_markdown_report(db, investigation_id)
    if format == "markdown":
        return ReportResponse(
            investigation_id=investigation_id,
            format="markdown",
            content=markdown,
        )
    if format == "pdf":
        pdf_bytes = build_pdf_from_markdown(markdown)
        return ReportResponse(
            investigation_id=investigation_id,
            format="pdf",
            content=base64.b64encode(pdf_bytes).decode("utf-8"),
        )
    raise HTTPException(status_code=400, detail="Invalid format")

