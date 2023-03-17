import unittest
from unittest import mock
from contextlib import redirect_stdout
from io import StringIO
from agent import main_loop
from parameterized import parameterized
from unittest.mock import MagicMock, patch
from types import SimpleNamespace
from agent import truncate_text, handle_code_snippet, generate_ai_response, main_loop

class TestApp(unittest.TestCase):

    def test_truncate_text(self):
        long_text = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6\nLine 7\nLine 8\nLine 9\nLine 10\nLine 11"
        truncated_text = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6\nLine 7\nLine 8\nLine 9\nLine 10"
        self.assertEqual(truncate_text(long_text, max_lines=10), truncated_text)

    def test_handle_code_snippet(self):
        response = "@CODE-SNIPPET: print('Hello, World!')"
        is_code_snippet, code_snippet = handle_code_snippet(response)
        self.assertTrue(is_code_snippet)

        response = "AI: AI: AI: AI: Hello, World!"
        is_code_snippet, code_snippet = handle_code_snippet(response)
        self.assertFalse(is_code_snippet)
        self.assertIsNone(code_snippet)

    @patch("openai.Completion.create")
    def test_generate_ai_response(self, mock_create):
        # Set up a mock response for the OpenAI API call
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].text = "AI: Hello, World!"
        mock_create.return_value = mock_response

        # Call the generate_ai_response function
        prompt = "Hello, how are you?"
        conversation_history = []
        response = generate_ai_response(prompt, conversation_history)

        # Check if the response is as expected
        self.assertEqual(response, "Hello, World!")

    @parameterized.expand([
        ("print(1 / 0)asdaasasasdadasasd",),
        ("print(undefined_variable)",),
        ("print('Hello'[100])",),
    ])
    def test_handle_code_snippet_with_errors(self, code_snippet):
        world_context_prompt = "In this world, you are an AI language model. You can provide code snippets as answers."
        loop_prompt_success = "Please provide me with another code snippet."
        loop_prompt_error = "That code snippet didn't work. Error: {error}. Please try again."

        response_mock = MagicMock()
        response_mock.choices = [MagicMock()]
        response_mock.choices[0].text = "@CODE-SNIPPET: " + code_snippet

        with unittest.mock.patch("agent.openai.Completion.create", return_value=response_mock):
            with redirect_stdout(StringIO()) as captured_output:
                main_loop(world_context_prompt, loop_prompt_success, loop_prompt_error, 1)

            output = captured_output.getvalue()
            self.assertIn("Error:", output)




if __name__ == "__main__":
    unittest.main()
