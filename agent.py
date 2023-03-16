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

world_context_prompt = config["Prompts"]["world_context_prompt"]
loop_prompt_success = config["Prompts"]["loop_prompt_success"]
loop_prompt_error = config["Prompts"]["loop_prompt_error"]
num_iterations = config["Settings"]["num_iterations"]

conversation_history = []

console = Console()

# Add message to conversation history
def add_to_history(role, content):
    message = {"role": role, "content": content}
    conversation_history.append(message)

# Ask DaVinci for a response based on the prompt and conversation history
def ask_davinci(prompt, conversation_history):
    history = "".join([f"{msg['role']}: {msg['content']}\n" for msg in conversation_history])
    console.print(f"AI Prompt: {prompt}")

    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"{history}\nAI: {prompt}\n",
        max_tokens=500,
        n=1,
        stop=None,
        temperature=0.7,
    )

    answer = response.choices[0].text.strip()
    return answer

# Execute code and return output and success status

def execute_code(code):
    console.print(f"Executing: {code}")

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
        success = result.returncode == 0

    except subprocess.TimeoutExpired:
        stdout_output = ""
        stderr_output = "Error: Code execution timed out."
        success = False

    finally:
        os.remove(temp_file.name)

    output = f"STDOUT:\n{stdout_output}\nSTDERR:\n{stderr_output}"
    return output, success

# Main loop

# Main loop
def main_loop(world_context_prompt, loop_prompt_success, loop_prompt_error, num_iterations):
    response = ask_davinci(world_context_prompt, conversation_history)

    add_to_history("User", world_context_prompt)
    add_to_history("AI", response)

    console.print(f"User: [user]{world_context_prompt}\n[/user]AI: [ai]{response}[/ai]")

    success = False  # Initialize success variable here

    for _ in range(num_iterations):
        response = ask_davinci(loop_prompt_success if success else loop_prompt_error, conversation_history)
        add_to_history("AI", response)
        console.print(f"AI: [ai]{response}[/ai]")

        if response.startswith("@CODE-SNIPPET:"):
            code = response.replace("@CODE-SNIPPET:", "").strip()
            syntax_code = Syntax(code, "python", theme="monokai", line_numbers=True)
            console.print(f"Code:\n{syntax_code}")
            result, success = execute_code(code)
            console.print(f"Output:\n[output]{result}[/output]")

            if not success:
                loop_prompt_error = loop_prompt_error.format(error=result.split("\n", 1)[0])
            else:
                loop_prompt_error = loop_prompt_error.format(error="")
        else:
            loop_prompt_error = loop_prompt_error.format(error="")


if __name__ == "__main__":
    use_default = input("Do you want to use the default world context prompt? (yes/no): ").lower()
    if use_default == "no" or use_default == "n":
        world_context_prompt = input("Please enter your custom world context prompt: ")

    main_loop(world_context_prompt, loop_prompt_success, loop_prompt_error, num_iterations)
    summary_prompt = config["Prompts"]["summary_prompt"]
    summary_response = ask_davinci(summary_prompt, conversation_history)
    add_to_history("User", summary_prompt)
    add_to_history("AI", summary_response)

    console.print(f"User: {summary_prompt}\nAI: {summary_response}")
    sys.exit(0)

