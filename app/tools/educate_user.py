import json
import random
from pathlib import Path

from app.mcp import tool
from app.models.quiz import QuizQuestion, QuizRequest, QuizResponse, QuizResult
from app.services.cache import cache_service

_quiz_data_path = Path(__file__).parent.parent / "data" / "quiz.json"
with open(_quiz_data_path, "r") as f:
    _raw_quiz_data = json.load(f)
    QUIZ_QUESTIONS = [
        {**q, "id": i} for i, q in enumerate(_raw_quiz_data)
    ]


async def _get_user_streak(user_id: str) -> int:
    key = f"quiz_streak:{user_id}"
    streak = await cache_service.get(key)
    return int(streak) if streak is not None else 0


async def _update_user_streak(user_id: str, correct: bool) -> int:
    key = f"quiz_streak:{user_id}"
    if not correct:
        await cache_service.set(key, 0, expire=86400)  # 24h
        return 0

    # Use INCR to handle race conditions and simplify logic
    async with cache_service.get_client() as client:
        new_streak = await client.incr(key)
        await client.expire(key, 86400)
        return new_streak


@tool
async def play_quiz(request: QuizRequest) -> QuizResponse:
    """
    Manages an educational quiz game for users.

    It serves questions and tracks user streaks in Redis.
    If an answer is submitted, it is checked, and the result is returned.
    """
    last_result: QuizResult | None = None

    if request.question_id is not None and request.answer is not None:
        question_data = next((q for q in QUIZ_QUESTIONS if q["id"] == request.question_id), None)
        if question_data:
            is_correct = request.answer == question_data["answer"]
            await _update_user_streak(request.user_id, is_correct)
            last_result = QuizResult(
                correct=is_correct,
                correct_answer=question_data["answer"],
                explanation=question_data["explanation"],
            )

    current_streak = await _get_user_streak(request.user_id)

    # Serve a random next question
    next_question_data = random.choice(QUIZ_QUESTIONS)

    return QuizResponse(
        user_id=request.user_id,
        streak=current_streak,
        next_question=QuizQuestion(
            id=next_question_data["id"],
            question=next_question_data["question"],
            options=next_question_data["options"],
        ),
        last_result=last_result,
    )
