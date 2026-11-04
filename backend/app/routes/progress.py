"""Progress analytics and the skill gap roadmap.

Every endpoint requires a logged-in user and only uses that user's own data.
"""
from fastapi import APIRouter, Depends

from app.database import repositories
from app.routes.auth import get_current_user
from app.schemas.progress import (
    ProgressOut,
    RoadmapOut,
    SessionPoint,
    TopicPerformance,
)
from app.services import roadmap_service

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("", response_model=ProgressOut)
def get_progress(user: dict = Depends(get_current_user)) -> ProgressOut:
    user_id = user["id"]
    sessions = repositories.list_sessions(user_id)
    points = repositories.session_points(user_id)
    topics = repositories.topic_stats(user_id)

    scores = [p["overall_score"] for p in points]
    average = round(sum(scores) / len(scores), 1) if scores else None
    improvement = round(scores[-1] - scores[0], 1) if len(scores) >= 2 else None

    return ProgressOut(
        total_sessions=len(sessions),
        completed_sessions=len(points),
        total_answers=sum(s["answered_count"] for s in sessions),
        average_score=average,
        best_score=round(max(scores), 1) if scores else None,
        latest_score=round(scores[-1], 1) if scores else None,
        improvement=improvement,
        strongest_topic=topics[-1]["topic"] if topics else None,
        weakest_topic=topics[0]["topic"] if topics else None,
        sessions=[
            SessionPoint(
                session_id=p["id"],
                label=p["created_at"][:10],
                role=p["role"],
                overall_score=round(p["overall_score"], 1),
            )
            for p in points
        ],
        topics=[
            TopicPerformance(
                topic=t["topic"],
                average_score=round(t["average_score"], 1),
                attempts=t["attempts"],
            )
            for t in topics
        ],
    )


@router.get("/roadmap", response_model=RoadmapOut)
def get_roadmap(user: dict = Depends(get_current_user)) -> RoadmapOut:
    return roadmap_service.build_roadmap(user["id"])