"""Regression tests for saved Blockly sequence storage."""

import json
import tempfile
import unittest
from pathlib import Path

from webapp import server


def response_body(response):
    return json.loads(response.body)


class SequenceStorageTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.sequences_directory = Path(self.temporary_directory.name)
        self.original_sequences_directory = server.SEQUENCES_DIR
        server.SEQUENCES_DIR = self.sequences_directory

    def tearDown(self):
        server.SEQUENCES_DIR = self.original_sequences_directory
        self.temporary_directory.cleanup()

    def test_save_list_and_load_round_trip(self):
        workspace = {
            "blocks": {
                "languageVersion": 0,
                "blocks": [{"type": "math_number", "id": "one"}],
            },
        }

        saved = server.api_sequences_save(
            "Relay validation",
            server.SequenceSaveRequest(workspace=workspace),
        )

        self.assertEqual(response_body(saved), {
            "status": "ok",
            "name": "Relay validation",
        })
        self.assertEqual(
            response_body(server.api_sequences_list()),
            ["Relay validation"],
        )
        self.assertEqual(
            response_body(server.api_sequences_get("Relay validation")),
            workspace,
        )

    def test_save_replaces_file_atomically_with_complete_json(self):
        first_workspace = {"blocks": {"blocks": []}}
        second_workspace = {"blocks": {"blocks": [{"type": "controls_if"}]}}

        server.api_sequences_save(
            "Repeated save",
            server.SequenceSaveRequest(workspace=first_workspace),
        )
        server.api_sequences_save(
            "Repeated save",
            server.SequenceSaveRequest(workspace=second_workspace),
        )

        stored_path = self.sequences_directory / "Repeated save.json"
        self.assertEqual(
            json.loads(stored_path.read_text(encoding="utf-8")),
            second_workspace,
        )
        self.assertFalse(
            (self.sequences_directory / "Repeated save.json.tmp").exists()
        )

    def test_invalid_or_unaddressable_sequence_names_are_rejected(self):
        response = server.api_sequences_save(
            "../outside",
            server.SequenceSaveRequest(workspace={}),
        )
        self.assertEqual(response.status_code, 400)

        (self.sequences_directory / "not@addressable.json").write_text(
            "{}",
            encoding="utf-8",
        )
        self.assertEqual(response_body(server.api_sequences_list()), [])


if __name__ == "__main__":
    unittest.main()
