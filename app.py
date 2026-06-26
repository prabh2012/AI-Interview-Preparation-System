from flask import Flask, render_template, request, session, jsonify, redirect, url_for
import pandas as pd
import random

app = Flask(__name__)
app.secret_key = "ai_interview_secret"

# ---------------- LOAD DATASET ----------------
df = pd.read_csv("Question_dataset.csv")

# Clean role column
df["role"] = (
    df["role"]
    .fillna("")
    .astype(str)
    .str.strip()
)

# Remove invalid rows
df = df[
    ~df["role"].str.lower().isin(
        ["", "nan", "none"]
    )
]

roles = sorted(
    df["role"]
    .unique()
    .tolist()
)

# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template(
        "index.html",
        roles=roles
    )


# ---------------- START INTERVIEW ----------------
@app.route('/start', methods=['POST'])
def start():

    role = request.form.get("role")

    if not role:
        return redirect(url_for("home"))

    questions = df[
        df["role"] == role
    ]["question"].tolist()

    if len(questions) == 0:
        return redirect(url_for("home"))

    selected_questions = random.sample(
        questions,
        min(5, len(questions))
    )

    session["role"] = role
    session["questions"] = selected_questions
    session["index"] = 0
    session["history"] = []

    return render_template(
        "interview.html",
        role=role,
        question=selected_questions[0],
        index=1,
        total=len(selected_questions)
    )


# ---------------- EVALUATE ANSWER ----------------
@app.route('/evaluate', methods=['POST'])
def evaluate():

    data = request.get_json()

    question = data.get("question", "")
    answer = data.get("answer", "").lower()

    if answer.strip() == "":
        return jsonify({
            "score": 0,
            "feedback": "No answer provided."
        })

    score = 0

    words = len(answer.split())

    if words >= 5:
        score += 20

    if words >= 10:
        score += 20

    if words >= 20:
        score += 20

    keywords = [
        "data",
        "analysis",
        "python",
        "tableau",
        "power bi",
        "database",
        "visualization",
        "dashboard",
        "algorithm",
        "machine learning",
        "example",
        "because"
    ]

    matched = 0

    for word in keywords:
        if word in answer:
            matched += 5

    score += matched

    if score > 100:
        score = 100

    # Dynamic feedback
    if score >= 80:
        feedback = (
            "Excellent answer. Your explanation is detailed and demonstrates strong understanding."
        )

    elif score >= 60:
        feedback = (
            "Good answer. Try adding practical examples and technical depth."
        )

    elif score >= 40:
        feedback = (
            "Basic understanding shown. Expand your explanation for better clarity."
        )

    else:
        feedback = (
            "Your answer is too short. Explain the concept with examples."
        )

    history = session.get("history", [])

    history.append({
        "question": question,
        "answer": answer,
        "score": score,
        "feedback": feedback
    })

    session["history"] = history

    return jsonify({
        "score": score,
        "feedback": feedback
    })


# ---------------- NEXT QUESTION ----------------
@app.route('/next')
def next_question():

    session["index"] += 1

    if session["index"] >= len(session["questions"]):
        return jsonify({
            "done": True
        })

    return jsonify({
        "done": False,
        "question": session["questions"][session["index"]],
        "index": session["index"] + 1,
        "total": len(session["questions"])
    })


# ---------------- RESULT ----------------
@app.route('/result')
def result():

    history = session.get("history", [])

    average_score = 0

    if history:
        average_score = round(
            sum(item["score"] for item in history)
            / len(history)
        )

    return render_template(
        "result.html",
        role=session.get("role", "Unknown"),
        score=average_score,
        history=history
    )


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(
        debug=True,
        port=5001
    )