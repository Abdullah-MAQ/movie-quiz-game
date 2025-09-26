import os
import pathlib
import uuid
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from semantic_kernel_client import QuizGenerator
from quiz_service import QuizManager
from typing import Dict, Any

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

RAW_DATASET_PATH = os.getenv("MOVIE_DATASET", os.path.join(os.path.dirname(__file__), "movies.csv"))
DATASET_PATH = str(pathlib.Path(RAW_DATASET_PATH).resolve())
print(f"[backend] Using dataset: {DATASET_PATH}")

quiz_generator = QuizGenerator(csv_path=DATASET_PATH)
quiz_manager = QuizManager(quiz_generator)

# Simple in-memory user storage (in production, use a proper database)
users: Dict[str, Dict[str, Any]] = {}
# User scores and stats storage
user_scores: Dict[str, Dict[str, Any]] = {}


@app.route("/api/auth/register", methods=["POST"])
def register_user():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request data"}), 400
    
    email = data.get("email")
    password = data.get("password")
    preferred_genre = data.get("preferred_genre")
    
    if not email or not password or not preferred_genre:
        return jsonify({"error": "Email, password, and preferred genre are required"}), 400
    
    # Check if user already exists
    if email in users:
        return jsonify({"error": "User already exists"}), 409
    
    # Create new user
    user_id = str(uuid.uuid4())
    users[email] = {
        "user_id": user_id,
        "email": email,
        "password": password,  # In production, hash this!
        "preferred_genre": preferred_genre,
        "display_name": email.split('@')[0],  # Use email prefix as display name
        "created_at": "2025-09-18"  # In production, use actual timestamp
    }
    
    # Initialize user scores
    user_scores[user_id] = {
        "total_score": 0,
        "quizzes_played": 0,
        "correct_answers": 0,
        "current_streak": 0,
        "longest_streak": 0,
        "best_score": 0
    }
    
    return jsonify({
        "message": "User registered successfully",
        "user_id": user_id,
        "preferred_genre": preferred_genre
    }), 201


@app.route("/api/auth/login", methods=["POST"])
def login_user():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request data"}), 400
    
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    
    user = users.get(email)
    if not user or user["password"] != password:
        return jsonify({"error": "Invalid credentials"}), 401
    
    return jsonify({
        "message": "Login successful",
        "user_id": user["user_id"],
        "email": user["email"],
        "preferred_genre": user["preferred_genre"]
    }), 200


@app.route("/api/quiz/start", methods=["POST"])
def start_quiz():
    data = request.get_json(silent=True) or {}
    total_questions = int(data.get("total_questions", 10))
    user_id = data.get("user_id")
    preferred_genre = None
    
    # Find user's preferred genre if user_id is provided
    if user_id:
        for user_data in users.values():
            if user_data["user_id"] == user_id:
                preferred_genre = user_data["preferred_genre"]
                break
    
    resp = quiz_manager.start_session(total_questions=total_questions, preferred_genre=preferred_genre, user_id=user_id)
    return jsonify(resp)


@app.route("/api/quiz/answer", methods=["POST"])
def answer_question():
    data = request.get_json(force=True)
    session_id = data.get("session_id")
    question_id = data.get("question_id")
    answer_index = int(data.get("answer_index", -1))
    time_left = int(data.get("time_left", 0))
    if session_id is None or question_id is None:
        return jsonify({"error": "Missing required fields"}), 400
    # Allow answer_index = -1 for timeouts, but validate it's not less than -1
    if answer_index < -1:
        return jsonify({"error": "Invalid answer index"}), 400
    resp = quiz_manager.answer_question(session_id, question_id, answer_index, time_left)
    status = 200 if "error" not in resp else 400
    return jsonify(resp), status


@app.route("/api/quiz/complete", methods=["POST"])
def complete_quiz():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request data"}), 400
    
    session_id = data.get("session_id")
    final_score = data.get("final_score", 0)
    correct_answers = data.get("correct_answers", 0)
    total_questions = data.get("total_questions", 0)
    
    # Find the session to get user_id
    session = quiz_manager.sessions.get(session_id)
    if not session:
        return jsonify({"error": "Invalid session"}), 400
    
    user_id = session.user_id
    if user_id and user_id in user_scores:
        stats = user_scores[user_id]
        stats["total_score"] += final_score
        stats["quizzes_played"] += 1
        stats["correct_answers"] += correct_answers
        if final_score > stats["best_score"]:
            stats["best_score"] = final_score
        
        # Simple streak logic (would need proper date tracking in production)
        if correct_answers > total_questions / 2:  # More than 50% correct
            stats["current_streak"] += 1
            if stats["current_streak"] > stats["longest_streak"]:
                stats["longest_streak"] = stats["current_streak"]
        else:
            stats["current_streak"] = 0
    
    return jsonify({"message": "Quiz completed successfully"}), 200


@app.route("/api/leaderboard", methods=["GET"])
def get_leaderboard():
    # Create leaderboard from registered users
    leaderboard = []
    
    for email, user_data in users.items():
        user_id = user_data["user_id"]
        stats = user_scores.get(user_id, {})
        
        leaderboard.append({
            "user_id": user_id,
            "name": user_data.get("display_name", email.split('@')[0]),
            "email": email,
            "preferred_genre": user_data.get("preferred_genre", ""),
            "total_score": stats.get("total_score", 0),
            "quizzes_played": stats.get("quizzes_played", 0),
            "current_streak": stats.get("current_streak", 0),
            "best_score": stats.get("best_score", 0)
        })
    
    # Sort by total score (descending)
    leaderboard.sort(key=lambda x: x["total_score"], reverse=True)
    
    # Add ranks
    for i, entry in enumerate(leaderboard):
        entry["rank"] = i + 1
    
    return jsonify({"leaderboard": leaderboard[:20]}), 200  # Top 20


@app.route("/api/profile/<user_id>", methods=["GET"])
def get_user_profile(user_id):
    # Find user by user_id
    user_data = None
    user_email = None
    
    for email, data in users.items():
        if data["user_id"] == user_id:
            user_data = data
            user_email = email
            break
    
    if not user_data:
        return jsonify({"error": "User not found"}), 404
    
    stats = user_scores.get(user_id, {})
    
    profile = {
        "user_id": user_id,
        "email": user_email,
        "display_name": user_data.get("display_name", user_email.split('@')[0]),
        "preferred_genre": user_data.get("preferred_genre", ""),
        "created_at": user_data.get("created_at", "2025-09-18"),
        "total_score": stats.get("total_score", 0),
        "quizzes_played": stats.get("quizzes_played", 0),
        "correct_answers": stats.get("correct_answers", 0),
        "current_streak": stats.get("current_streak", 0),
        "longest_streak": stats.get("longest_streak", 0),
        "best_score": stats.get("best_score", 0)
    }
    
    return jsonify({"profile": profile}), 200


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"[backend] Starting Flask on port {port} (debug disabled)")
    app.run(host="0.0.0.0", port=port, debug=False)
