import unittest
from unittest.mock import patch

import app as game
from app import PRIZES
import questions as question_data
from questions import (
    DICAS,
    NIVEIS,
    PERGUNTAS,
    PERGUNTAS_POR_NIVEL,
    RESPOSTAS_CERTAS,
    RESPOSTAS_ERRADAS_1,
    RESPOSTAS_ERRADAS_2,
    RESPOSTAS_ERRADAS_3,
)


class GameTests(unittest.TestCase):
    def setUp(self):
        game.app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.original_questions = game.QUESTIONS
        game.QUESTIONS = [
            [
                {
                    "id": row,
                    "text": f"Pergunta de teste do nível {level + 1}, questão {row + 1}?",
                    "options": ["A", "B", "C", "D"],
                    "correct_index": 0,
                    "hint": "Dica de teste.",
                }
                for row in range(2)
            ]
            for level in range(NIVEIS)
        ]
        self.client = game.app.test_client()

    def tearDown(self):
        game.QUESTIONS = self.original_questions

    def get_question_id(self):
        with self.client.session_transaction() as game_session:
            return game_session["question_id"]

    def answer_current(self, correct=True):
        with self.client.session_transaction() as game_session:
            level = game_session["level"]
            question_id = game_session["question_id"]
            question = next(item for item in game.QUESTIONS[level] if item["id"] == question_id)
            option_order = game_session["option_order"]
            correct_index = option_order.index(question["correct_index"])
            answer = correct_index if correct else (correct_index + 1) % 4
        return self.client.post("/action", data={"action": "answer", "answer": str(answer)})

    def test_question_and_answer_arrays_have_50_slots_per_level(self):
        arrays = (
            PERGUNTAS,
            RESPOSTAS_CERTAS,
            RESPOSTAS_ERRADAS_1,
            RESPOSTAS_ERRADAS_2,
            RESPOSTAS_ERRADAS_3,
            DICAS,
        )
        self.assertTrue(all(len(array) == NIVEIS for array in arrays))
        for level in range(NIVEIS):
            for array in arrays:
                self.assertEqual(len(array[level]), PERGUNTAS_POR_NIVEL)
                populated_count = 50 if array is not DICAS else 0
                self.assertTrue(all(value is not None for value in array[level][:populated_count]))
                self.assertTrue(all(value is None for value in array[level][populated_count:]))

    def test_provided_question_bank_has_expected_questions_per_level(self):
        self.assertEqual(len(question_data.QUESTIONS), NIVEIS)
        expected_counts = [50] * NIVEIS
        for level, expected_count in zip(question_data.QUESTIONS, expected_counts):
            self.assertEqual(len(level), expected_count)
            for question in level:
                self.assertEqual(len(question["options"]), 4)
                self.assertEqual(len(set(question["options"])), 4)
                self.assertEqual(question["correct_index"], 0)

    def test_question_and_three_wrong_answers_are_combined_by_same_position(self):
        question = "Pergunta cadastrada para teste?"
        arrays = (
            (question_data.PERGUNTAS, question),
            (question_data.RESPOSTAS_CERTAS, "Correta"),
            (question_data.RESPOSTAS_ERRADAS_1, "Errada 1"),
            (question_data.RESPOSTAS_ERRADAS_2, "Errada 2"),
            (question_data.RESPOSTAS_ERRADAS_3, "Errada 3"),
            (question_data.DICAS, "Uma dica."),
        )
        original_values = [array[8][7] for array, _ in arrays]
        try:
            for array, value in arrays:
                array[8][7] = value
            loaded = next(
                question
                for question in question_data.build_question_bank()[8]
                if question["id"] == "nivel-9-linha-8"
            )
        finally:
            for (array, _), original_value in zip(arrays, original_values):
                array[8][7] = original_value

        self.assertEqual(loaded["id"], "nivel-9-linha-8")
        self.assertEqual(loaded["text"], question)
        self.assertCountEqual(loaded["options"], ["Correta", "Errada 1", "Errada 2", "Errada 3"])
        self.assertEqual(loaded["correct_index"], 0)

    def test_incomplete_parallel_arrays_are_rejected(self):
        original_answer = question_data.RESPOSTAS_ERRADAS_1[9][5]
        try:
            question_data.RESPOSTAS_ERRADAS_1[9][5] = None
            with self.assertRaisesRegex(ValueError, "RESPOSTAS_ERRADAS_1"):
                question_data.build_question_bank()
        finally:
            question_data.RESPOSTAS_ERRADAS_1[9][5] = original_answer

    def test_empty_level_shows_instructions_instead_of_starting_a_broken_game(self):
        game.QUESTIONS = [[] for _ in range(NIVEIS)]
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Este n\xc3\xadvel ainda n\xc3\xa3o tem perguntas", response.data)

    def test_refresh_keeps_same_question_and_skip_changes_it(self):
        self.client.get("/")
        original_id = self.get_question_id()
        with self.client.session_transaction() as game_session:
            original_order = list(game_session["option_order"])
        self.client.get("/")
        self.assertEqual(self.get_question_id(), original_id)
        with self.client.session_transaction() as game_session:
            self.assertEqual(game_session["option_order"], original_order)

        with patch("app.random.shuffle", side_effect=lambda options: options.reverse()):
            response = self.client.post("/action", data={"action": "skip"})
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(self.get_question_id(), original_id)
        with self.client.session_transaction() as game_session:
            self.assertEqual(game_session["skips"], 2)
            self.assertEqual(game_session["option_order"], [3, 2, 1, 0])

    def test_half_and_hint_help_controls(self):
        self.client.get("/")
        self.client.post("/action", data={"action": "half"})
        with self.client.session_transaction() as game_session:
            hidden = game_session["hidden_options"]
            self.assertEqual(len(hidden), 2)
            self.assertTrue(game_session["half_used"])
            question = next(item for item in game.QUESTIONS[0] if item["id"] == game_session["question_id"])
            self.assertNotIn(
                game_session["option_order"].index(question["correct_index"]),
                hidden,
            )

        response = self.client.post("/action", data={"action": "hint"})
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as game_session:
            self.assertTrue(game_session["hint_visible"])
            self.assertTrue(game_session["hint_used"])

        self.answer_current()
        with self.client.session_transaction() as game_session:
            self.assertTrue(game_session["half_used"])
            self.assertTrue(game_session["hint_used"])
            self.assertEqual(game_session["level"], 1)

    def test_hint_without_registered_text_is_not_consumed(self):
        for question in game.QUESTIONS[0]:
            question["hint"] = ""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name="action" value="hint" disabled', response.data)

        self.client.post("/action", data={"action": "hint"})
        with self.client.session_transaction() as game_session:
            self.assertFalse(game_session["hint_used"])

    def test_correct_answers_progress_and_complete_the_game(self):
        self.client.get("/")
        for level in range(10):
            self.answer_current()
            if level < 9:
                with self.client.session_transaction() as game_session:
                    self.assertEqual(game_session["level"], level + 1)
                    self.assertEqual(game_session["earned"], PRIZES[level])
        response = self.client.get("/result")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Voc\xc3\xaa chegou ao milh\xc3\xa3o", response.data)

    def test_wrong_answer_and_stop_show_results(self):
        self.client.get("/")
        response = self.answer_current(correct=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/result")
        self.assertEqual(self.client.get("/").status_code, 302)

        self.client.post("/restart")
        response = self.client.post("/action", data={"action": "stop"})
        self.assertEqual(response.location, "/result")
        self.assertEqual(self.client.get("/result").status_code, 200)


if __name__ == "__main__":
    unittest.main()
