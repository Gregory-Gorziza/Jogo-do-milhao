import os
import random
import secrets

from flask import Flask, redirect, render_template, request, session, url_for

from questions import QUESTIONS


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)

PRIZES = [1_000, 2_500, 5_000, 10_000, 25_000, 50_000, 100_000, 250_000, 500_000, 1_000_000]
STARTING_SKIPS = 3


def start_game():
    session.clear()
    session.update(
        level=0,
        question_id=None,
        earned=0,
        skips=STARTING_SKIPS,
        half_used=False,
        hint_used=False,
        hidden_options=[],
        hint_visible=False,
        option_order=[],
    )
    select_question()


def select_question(exclude_id=None):
    level = session["level"]
    choices = [question for question in QUESTIONS[level] if question["id"] != exclude_id]
    if not choices:
        session["question_id"] = None
        session["hidden_options"] = []
        session["hint_visible"] = False
        return False
    question = random.choice(choices)
    session["question_id"] = question["id"]
    option_order = list(range(len(question["options"])))
    random.shuffle(option_order)
    session["option_order"] = option_order
    session["hidden_options"] = []
    session["hint_visible"] = False
    return True


def current_question():
    question_id = session.get("question_id")
    level = session.get("level")
    if not isinstance(level, int) or not 0 <= level < len(QUESTIONS):
        return None
    question = next((question for question in QUESTIONS[level] if question["id"] == question_id), None)
    option_order = session.get("option_order")
    if question is None or not isinstance(option_order, list):
        return None
    if sorted(option_order) != list(range(len(question["options"]))):
        return None

    return {
        **question,
        "options": [question["options"][index] for index in option_order],
        "correct_index": option_order.index(question["correct_index"]),
    }


def finish_game(outcome, prize):
    session["result"] = {"outcome": outcome, "prize": prize}
    return redirect(url_for("result"))


@app.get("/")
def index():
    if session.get("result"):
        return redirect(url_for("result"))
    if "level" not in session:
        start_game()
    question = current_question()
    if question is None:
        return render_template(
            "setup.html",
            level=session["level"],
            level_count=len(QUESTIONS),
        )
    return render_template(
        "index.html",
        question=question,
        level=session["level"],
        level_count=len(QUESTIONS),
        prize=PRIZES[session["level"]],
        earned=session["earned"],
        skips=session["skips"],
        half_available=not session["half_used"],
        hint_available=not session["hint_used"] and bool(question["hint"]),
        hidden_options=session["hidden_options"],
        hint_visible=session["hint_visible"],
    )


@app.post("/action")
def action():
    if session.get("result"):
        return redirect(url_for("result"))
    if "level" not in session:
        start_game()
        return redirect(url_for("index"))

    question = current_question()
    if question is None:
        return redirect(url_for("index"))

    action_name = request.form.get("action")
    if action_name == "answer":
        try:
            answer_index = int(request.form.get("answer", ""))
        except ValueError:
            return redirect(url_for("index"))
        if not 0 <= answer_index < len(question["options"]) or answer_index in session["hidden_options"]:
            return redirect(url_for("index"))

        if answer_index != question["correct_index"]:
            return finish_game("wrong", session["earned"])

        session["earned"] = PRIZES[session["level"]]
        if session["level"] == len(QUESTIONS) - 1:
            return finish_game("win", session["earned"])

        session["level"] += 1
        select_question()
        return redirect(url_for("index"))

    if action_name == "stop":
        return finish_game("stop", session["earned"])

    if action_name == "skip" and session["skips"] > 0:
        if select_question(exclude_id=question["id"]):
            session["skips"] -= 1
    elif action_name == "half" and not session["half_used"]:
        wrong_indices = [
            index for index in range(len(question["options"]))
            if index != question["correct_index"]
        ]
        session["hidden_options"] = random.sample(wrong_indices, 2)
        session["half_used"] = True
    elif action_name == "hint" and not session["hint_used"] and question["hint"]:
        session["hint_used"] = True
        session["hint_visible"] = True
    return redirect(url_for("index"))


@app.get("/result")
def result():
    result_data = session.get("result")
    if not result_data:
        return redirect(url_for("index"))
    return render_template("result.html", result=result_data)


@app.post("/restart")
def restart():
    start_game()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
