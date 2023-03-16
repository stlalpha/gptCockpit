import unittest
from agent.py import sanitize_text, truncate_text  # Assuming your main code file is named app.py

class TestApp(unittest.TestCase):

    def test_sanitize_text(self):
        self.assertEqual(sanitize_text("AI: AI: AI: AI: Hello, World!"), "Hello, World!")
        self.assertEqual(sanitize_text("AI:AI:AI:AI:Hello, World!"), "Hello, World!")
        self.assertEqual(sanitize_text("AI: AI:AI: AI:Hello, World!"), "Hello, World!")
        self.assertEqual(sanitize_text("Hello, World!"), "Hello, World!")

    def test_truncate_text(self):
        input_text = "Line1\nLine2\nLine3\nLine4\nLine5\nLine6\nLine7\nLine8\nLine9\nLine10\nLine11\nLine12"
        expected_output = "Line1\nLine2\nLine3\nLine4\nLine5\nLine6\nLine7\nLine8\nLine9\nLine10"
        self.assertEqual(truncate_text(input_text, max_lines=10), expected_output)
        
        input_text = "Line1\nLine2\nLine3\nLine4\nLine5\nLine6\nLine7\nLine8\nLine9\nLine10"
        expected_output = "Line1\nLine2\nLine3\nLine4\nLine5\nLine6\nLine7\nLine8\nLine9\nLine10"
        self.assertEqual(truncate_text(input_text, max_lines=10), expected_output)

if __name__ == "__main__":
    unittest.main()
