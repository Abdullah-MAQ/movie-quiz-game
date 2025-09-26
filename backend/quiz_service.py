import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Any
from semantic_kernel_client import QuizGenerator


@dataclass
class QuizSession:
    session_id: str
    difficulty_level: int = 1  # 1 easy, 2 medium, 3 hard
    history: List[Dict[str, Any]] = field(default_factory=list)
    score: int = 0
    total_questions: int = 10
    questions_served: int = 0
    preferred_genre: str = None  # User's preferred movie genre
    user_id: str = None  # Associated user ID

    def adjust_difficulty(self):
        if len(self.history) == 0:
            return
        last_correct = self.history[-1].get("correct")
        if last_correct and self.difficulty_level < 3:
            self.difficulty_level += 1
        elif not last_correct and self.difficulty_level > 1:
            self.difficulty_level -= 1


class QuizManager:
    def __init__(self, generator: QuizGenerator):
        self.generator = generator
        self.sessions: Dict[str, QuizSession] = {}
        self._questions: Dict[str, Dict[str, Any]] = {}  # question_id -> data

    def start_session(self, total_questions: int = 10, preferred_genre: str = None, user_id: str = None) -> Dict[str, Any]:
        session_id = str(uuid.uuid4())
        session = QuizSession(session_id=session_id, total_questions=total_questions, preferred_genre=preferred_genre)
        session.user_id = user_id  # Store user_id in session
        self.sessions[session_id] = session
        question_payload = self._create_question(session)
        return {
            "session_id": session_id,
            "question": question_payload,
            "score": 0,
            "questions_remaining": session.total_questions - session.questions_served,
        }

    def _create_question(self, session: QuizSession) -> Dict[str, Any]:
        qdata = self.generator.generate_question(session.difficulty_level, session.history, session.preferred_genre)
        question_id = str(uuid.uuid4())
        self._questions[question_id] = qdata
        session.questions_served += 1
        return {
            "id": question_id,
            "question": qdata["question"],
            "options": qdata["options"],
            "difficulty": qdata.get("difficulty", "unknown"),
            "number": session.questions_served,
            "total": session.total_questions,
        }

    def answer_question(self, session_id: str, question_id: str, answer_index: int, time_left: int = 0) -> Dict[str, Any]:
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Invalid session"}
        qdata = self._questions.get(question_id)
        if not qdata:
            return {"error": "Invalid question"}
        correct_index = qdata["answer_index"]
        
        # Handle timeout case (answer_index = -1)
        is_timeout = answer_index == -1
        is_correct = answer_index == correct_index if not is_timeout else False
        
        # Score: base 100 * difficulty + bonus for remaining time (no score for timeouts)
        if is_correct and not is_timeout:
            session.score += 100 * session.difficulty_level + (time_left * 5)
        
        session.history.append({
            "question_id": question_id,
            "given": answer_index,
            "correct_index": correct_index,
            "correct": is_correct,
            "timeout": is_timeout,
            "difficulty_level": session.difficulty_level,
        })
        session.adjust_difficulty()
        # Determine if quiz complete
        if session.questions_served >= session.total_questions:
            return {
                "correct": is_correct,
                "correct_index": correct_index,
                "score": session.score,
                "quiz_complete": True,
            }
        # Otherwise next question
        next_question = self._create_question(session)
        return {
            "correct": is_correct,
            "correct_index": correct_index,
            "score": session.score,
            "quiz_complete": False,
            "next_question": next_question,
            "difficulty_level": session.difficulty_level,
            "questions_remaining": session.total_questions - session.questions_served,
        }
