from typing import List, Optional

from pydantic import BaseModel, Field


class QuizRequest(BaseModel):
    user_id: str = Field(..., description="A unique identifier for the user playing the quiz.")
    question_id: Optional[int] = Field(
        default=None, description="The ID of the question being answered."
    )
    answer: Optional[str] = Field(
        default=None, description="The user's submitted answer to the question."
    )


class QuizQuestion(BaseModel):
    id: int
    question: str
    options: List[str]


class QuizResult(BaseModel):
    correct: bool
    correct_answer: str
    explanation: str


class QuizResponse(BaseModel):
    user_id: str
    streak: int = Field(..., description="The user's current correct answer streak.")
    next_question: QuizQuestion
    last_result: Optional[QuizResult] = None
