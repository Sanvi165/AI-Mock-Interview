"""Skill Gap Roadmap: turn stored results into a prioritized study plan.

The roadmap is deterministic (no AI call), so it works in demo mode and is easy to explain.
It only uses the data of the user it is built for.
"""
import json
from collections import Counter

from app.database import repositories
from app.demo import sample_data
from app.schemas.progress import RoadmapItem, RoadmapOut
from app.services.evaluation_service import WEAK_TOPIC_THRESHOLD


def _urgency(average: float) -> str:
    if average < 50:
        return "High"
    if average < 65:
        return "Medium"
    return "Low"


def _missing_concepts(topic: str, user_id: int) -> list[str]:
    counter: Counter = Counter()
    for row in repositories.feedback_for_topic(topic, user_id):
        feedback = json.loads(row["feedback_json"])
        counter.update(c for c in feedback.get("missing_concepts", []) if c)
    return [concept for concept, _ in counter.most_common(5)]


def _practice_questions(topic: str, concepts: list[str], asked: set[str]) -> list[str]:
    practice = [
        entry["text"]
        for entry in sample_data.QUESTION_BANK
        if entry["topic"] == topic and entry["text"] not in asked
    ][:2]
    for concept in concepts[:2]:
        practice.append(f"Explain '{concept}' in the context of {topic} with a short example.")
    if not practice:
        practice.append(f"Explain the core ideas of {topic} and give one real-world example.")
    return practice[:4]


def build_roadmap(user_id: int) -> RoadmapOut:
    stats = repositories.topic_stats(user_id)
    total_answers = sum(s["attempts"] for s in stats)
    if not stats:
        return RoadmapOut(
            items=[],
            generated_from_answers=0,
            message="Complete at least one interview to get your roadmap.",
        )

    weak = [s for s in stats if s["average_score"] < WEAK_TOPIC_THRESHOLD]
    if not weak:
        return RoadmapOut(
            items=[],
            generated_from_answers=total_answers,
            message="No weak topics found. All topic averages are 70 or above. Try harder interviews.",
        )

    asked = repositories.asked_question_texts(user_id)
    items = []
    for rank, stat in enumerate(weak, start=1):  # already sorted weakest first
        average = round(stat["average_score"], 1)
        concepts = _missing_concepts(stat["topic"], user_id)
        items.append(
            RoadmapItem(
                topic=stat["topic"],
                priority=rank,
                urgency=_urgency(average),
                average_score=average,
                attempts=stat["attempts"],
                reason=(
                    f"Your average on {stat['topic']} is {average}/100 over "
                    f"{stat['attempts']} answer(s)."
                ),
                study_focus=concepts or [f"Revise the fundamentals of {stat['topic']}."],
                practice_questions=_practice_questions(stat["topic"], concepts, asked),
            )
        )
    return RoadmapOut(items=items, generated_from_answers=total_answers)