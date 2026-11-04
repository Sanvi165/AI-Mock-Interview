"""History endpoints: list, view, delete, download report, demo seed, delete-all (privacy).

Every endpoint requires a logged-in user and only touches that user's own data.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse

from app.database import repositories
from app.demo import sample_data
from app.routes.auth import get_current_user
from app.schemas.interview import SessionBase, SessionDetail
from app.services import evaluation_service, report_service

router = APIRouter(prefix="/api/history", tags=["history"])


def _detail_or_404(session_id: int, user_id: int) -> SessionDetail:
    session = repositories.get_session(session_id, user_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Interview session not found.")
    return evaluation_service.build_session_detail(
        session, repositories.get_results(session_id)
    )


@router.get("", response_model=list[SessionBase])
def list_history(user: dict = Depends(get_current_user)) -> list[SessionBase]:
    return [SessionBase(**s) for s in repositories.list_sessions(user["id"])]


@router.post("/demo-seed")
def seed_demo_data(user: dict = Depends(get_current_user)) -> dict:
    """Add 4 sample completed interviews so charts and the roadmap can be demonstrated."""
    return {"created": sample_data.seed_demo_history(user["id"])}


@router.delete("")
def delete_all_history(user: dict = Depends(get_current_user)) -> dict:
    """Privacy control: permanently delete all saved interview data."""
    return {"deleted": repositories.delete_all_data(user["id"])}


@router.get("/{session_id}", response_model=SessionDetail)
def get_history_item(session_id: int, user: dict = Depends(get_current_user)) -> SessionDetail:
    return _detail_or_404(session_id, user["id"])


@router.delete("/{session_id}")
def delete_history_item(session_id: int, user: dict = Depends(get_current_user)) -> dict:
    if not repositories.delete_session(session_id, user["id"]):
        raise HTTPException(status_code=404, detail="Interview session not found.")
    return {"deleted": 1}


@router.get("/{session_id}/report")
def download_report(session_id: int, user: dict = Depends(get_current_user)) -> PlainTextResponse:
    detail = _detail_or_404(session_id, user["id"])
    if detail.status != "completed":
        raise HTTPException(
            status_code=400, detail="Finish the interview before generating a report."
        )
    markdown = report_service.build_markdown_report(detail)
    return PlainTextResponse(
        markdown,
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="interview-report-{session_id}.md"'
        },
    )