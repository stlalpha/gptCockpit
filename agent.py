import configparser
import json
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

# read secrets
def load_env(file_path):
    env_vars = {}

    try:
        with open(file_path, 'r') as f:
            for line in f:
                key, value = line.strip().split('=', 1)
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
        with open(file_path, 'r') as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Error: Unable to read or parse configuration file '{file_path}'.")
        sys.exit(1)
    
    return config

config_file_path = "config.json"
config = read_config(config_file_path)

conversation_history = []

def print_and_track_conversation(role, content):
    conversation_history.append({"role": role, "content": content})
    print(f"{role}: {content}")

def sanitize_text(text):
    while text.startswith("AI:"):
        text = text[4:].lstrip()  # Remove the "AI: " prefix and any leading whitespace
    return text

def generate_ai_response(prompt, conversation_history):
    sanitized_history = []
    for msg in conversation_history:
        role, content = msg['role'], msg['content']
        content = sanitize_text(content)
        sanitized_history.append({"role": role, "content": content})
    
    history = "".join([f"{msg['role']}: {msg['content']}\n" for msg in sanitized_history])
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"{history}\n{prompt}\n",
        max_tokens=500,
        n=1,
        stop=None,
        temperature=0.5,
    )
    answer = response.choices[0].text.strip()
    answer = truncate_text(answer, max_lines=10)  # Truncate the answer to a maximum of 10 lines
    return answer

def truncate_text(text, max_lines=10):
    lines = text.splitlines()
    if len(lines) > max_lines:
        lines = lines[:max_lines]
    return '\n'.join(lines)

def execute_code(code):
    print(f"Executing: {code}")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp_file:
        temp_file.write(code)
        temp_file.flush()

    try:
        result = subprocess.run(
            ["python", temp_file.name],
            text=True,
            capture_output=True,
            timeout=10  # Set a timeout to prevent long-running or infinite loops
        )

        stdout_output = result.stdout
        stderr_output = result.stderr
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
    print_and_track_conversation("User", world_context_prompt)
    response = generate_ai_response(world_context_prompt, conversation_history)

    for i in range(num_iterations):
        if response.startswith("@CODE-SNIPPET:"):
            code_snippet = response[len("@CODE-SNIPPET:"):].strip()
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

        print_and_track_conversation("User", current_prompt)
        response = generate_ai_response(current_prompt, conversation_history)
        print_and_track_conversation("AI", response)

world_context_prompt = config["Prompts"]["world_context_prompt"]
loop_prompt_success = config["Prompts"]["loop_prompt_success"]
loop_prompt_error = config["Prompts"]["loop_prompt_error"]
num_iterations = config["Settings"]["num_iterations"]

if __name__ == "__main__":
    use_default = input("Do you want to use the default world context prompt? (yes/no): ").lower()
    if use_default == "no" or use_default == "n":
        world_context_prompt = input("Please enter your custom world context prompt: ")

    override_iterations = input("Do you want to override the default iteration count? (yes/no): ").lower()
    if override_iterations == "yes" or override_iterations == "y":
        num_iterations = int(input("Please enter the custom iteration count: "))

    main_loop(world_context_prompt, loop_prompt_success, loop_prompt_error, num_iterations)
    summary_prompt = config["Prompts"]["summary_prompt"]
    summary_response = generate_ai_response(summary_prompt, conversation_history)
    print(f"\nUser Prompt: {summary_prompt}\nAI Response: {summary_response}")
    sys.exit(0)
