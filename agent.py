import configparser
import json
import tokenize
import openai
import os
import sys
import traceback
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
from rich.console import Console
from rich.syntax import Syntax
import subprocess
import tempfile
import argparse
from contextlib import contextmanager
from unittest.mock import MagicMock, patch
from datetime import datetime
import tiktoken

#TODO get compressed bits stored as tapes and be able to load context.  be able to string them together and have only the pointer hot in the context window.  use sqlite or sqldb to store

# read secrets
def load_env(file_path):
    env_vars = {}

    try:
        with open(file_path, "r") as f:
            for line in f:
                key, value = line.strip().split("=", 1)
                env_vars[key] = value
    except FileNotFoundError:
        print(f"Error: Unable to read the .env file at '{file_path}'.")

    return env_vars


env_file_path = ".env"
env_vars = load_env(env_file_path)
openai_api_key = env_vars.get("OPENAI_API_KEY")
openai.api_key = openai_api_key

# Read configuration data from a JSON file
def read_config(file_path):
    try:
        with open(file_path, "r") as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Error: Unable to read or parse configuration file '{file_path}'.")
        sys.exit(1)

    return config


config_file_path = "config.json"
config = read_config(config_file_path)

conversation_history = []


@contextmanager
def use_fake_openai_api():
    original_create = openai.Completion.create

    def fake_create(*args, **kwargs):
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[
            0
        ].text = "AI: Here is a code snippet for you: print('Hello, World!')"
        return response

    openai.Completion.create = fake_create
    try:
        yield
    finally:
        openai.Completion.create = original_create


def generate_filename(prefix):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.txt"



def print_and_track_conversation(role, content, history_file):
    conversation_history.append({"role": role, "content": content})
    print(f"{role}: {content}")
    with open(history_file, 'a') as f:
        f.write(f"{role}: {content}\n")


def handle_code_snippet(response):
    if response.startswith("@CODE-SNIPPET:"):
        code_snippet = response[len("@CODE-SNIPPET:") :].strip()
        return True, code_snippet
    else:
        return False, None


def compress_conversation_history(conversation_history):
    history = "".join(
        [f"{msg['role']}: {msg['content']}\n" for msg in conversation_history]
    )
    prompt = (
        f"Please provide a summarized version of the following conversation:\n{history}"
    )

    # Call the AI to summarize the conversation
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=100,  # Adjust the max tokens based on your desired length
        n=1,
        stop=None,
        temperature=0.5,
    )
    summarized_history = response.choices[0].text.strip()
    return summarized_history


#encoding = tiktoken.get_encoding("r50k_base")


def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding("r50k_base")
    num_tokens = len(encoding.encode(string))
    return num_tokens


def generate_ai_response(prompt, conversation_history):
    max_history_tokens = (
        4096 - num_tokens_from_string(prompt, "r50k_base") - 50
    )  # Reserve some tokens for AI response
    history = "".join(
        [f"{msg['role']}: {msg['content']}\n" for msg in conversation_history]
    )
    token_count = num_tokens_from_string(history, "r50k_base")

    if token_count > max_history_tokens:
        print("Compressing conversation history...")
        summarized_history = compress_conversation_history(conversation_history)
        history = summarized_history

    full_prompt = f"{history}\nAI: {prompt}\n"
    token_count = num_tokens_from_string(full_prompt, "r50k_base")
    print(f"Token count: {token_count}")

    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=full_prompt,
        max_tokens=500,
        n=1,
        stop=None,
        temperature=0.5,
    )
    answer = response.choices[0].text.strip()

    # Remove the "AI: " prefix before adding the response to the conversation history
    while answer.startswith("AI:") or answer.startswith("AI: "):
        answer = answer.lstrip("AI:").lstrip()

    conversation_history.append({"role": "AI", "content": answer})
    return answer


def execute_code(code):
    def truncate_output(text, max_lines=10):
        lines = text.splitlines()
        if len(lines) > max_lines:
            lines = lines[:max_lines]
        return "\n".join(lines)

    print(f"Executing: {code}")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp_file:
        temp_file.write(code)
        temp_file.flush()

    try:
        result = subprocess.run(
            ["python", temp_file.name],
            text=True,
            capture_output=True,
            timeout=10,  # Set a timeout to prevent long-running or infinite loops
        )

        stdout_output = truncate_output(result.stdout)
        stderr_output = truncate_output(result.stderr)
        success = result.returncode == 0 and stdout_output.strip() != ""

    except subprocess.TimeoutExpired:
        stdout_output = ""
        stderr_output = "Error: Code execution timed out."
        success = False

    finally:
        os.remove(temp_file.name)

    output = f"STDOUT:\n{stdout_output}\nSTDERR:\n{stderr_output}"
    return output, success



def main_loop(world_context_prompt, loop_prompt_success, loop_prompt_error, num_iterations):
    uncompressed_filename = generate_filename("uncompressed_conversation")
    compressed_filename = generate_filename("compressed_conversation")
    
    print_and_track_conversation("User", world_context_prompt, uncompressed_filename)
    response = generate_ai_response(world_context_prompt, conversation_history)
    print_and_track_conversation("AI", response, uncompressed_filename)

    for i in range(num_iterations):
        if response.startswith("@CODE-SNIPPET:"):
            code_snippet = response[len("@CODE-SNIPPET:") :].strip()
            print("Executing code snippet...\n", code_snippet)

            output, success = execute_code(code_snippet)
            print("Code snippet output:\n", output)

            if success and output.strip():
                current_prompt = loop_prompt_success
            else:
                if not output.strip():
                    error_message = "No output was produced."
                else:
                    error_message = output.split("\n")[-2]
                current_prompt = loop_prompt_error.format(error=error_message)
                print("Error:", error_message)

            current_prompt = f"{current_prompt}\n{output}"
        else:
            current_prompt = response

        print_and_track_conversation("User", current_prompt, uncompressed_filename)
        response = generate_ai_response(current_prompt, conversation_history)
        print_and_track_conversation("AI", response, uncompressed_filename)




world_context_prompt = config["Prompts"]["world_context_prompt"]
loop_prompt_success = config["Prompts"]["loop_prompt_success"]
loop_prompt_error = config["Prompts"]["loop_prompt_error"]
num_iterations = config["Settings"]["num_iterations"]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the AI agent with a fake service or the real OpenAI API."
    )
    parser.add_argument(
        "--use-fake-api",
        action="store_true",
        help="Use the fake OpenAI API service instead of the real one.",
    )

    args = parser.parse_args()

    use_default = input(
        "Do you want to use the default world context prompt? (yes/no): "
    ).lower()
    if use_default == "no" or use_default == "n":
        world_context_prompt = input("Please enter your custom world context prompt: ")

    override_iterations = input(
        "Do you want to override the default iteration count? (yes/no): "
    ).lower()
    if override_iterations == "yes" or override_iterations == "y":
        num_iterations = int(input("Please enter the custom iteration count: "))

    if args.use_fake_api:
        with use_fake_openai_api():
            main_loop(
                world_context_prompt,
                loop_prompt_success,
                loop_prompt_error,
                num_iterations,
            )
    else:
        main_loop(
            world_context_prompt, loop_prompt_success, loop_prompt_error, num_iterations
        )

    summary_prompt = config["Prompts"]["summary_prompt"]
    summary_response = generate_ai_response(summary_prompt, conversation_history)
    print(f"\nUser Prompt: {summary_prompt}\nAI Response: {summary_response}")

    # Compress conversation history and save to a file
    compressed_filename = generate_filename("compressed_conversation")
    compressed_history = compress_conversation_history(conversation_history)
    with open(compressed_filename, 'w') as f:
        f.write(compressed_history)
    
    sys.exit(0)
