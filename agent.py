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
    console.print(f"\nUser Prompt: {prompt}")

    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"{history}\nAI: {prompt}\n",
        max_tokens=500,
        n=1,
        stop=None,
        temperature=0.5,
    )

    answer = response.choices[0].text.strip()
    print(f"Raw AI Response: {response.choices[0].text}")
    print(f"Stripped AI Response: {answer}")
    return answer


# Execute code and return output and success status

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

# Main loop

def main_loop(world_context_prompt, loop_prompt_success, loop_prompt_error, num_iterations):
    add_to_history("User", world_context_prompt)  # Add the world context prompt to the conversation history
    response = ask_davinci(world_context_prompt, conversation_history)  # Get the initial response based on the world context prompt

    if response.startswith("@CODE-SNIPPET:"):
        add_to_history("AI", response)
        code_snippet = response[len("@CODE-SNIPPET:"):].strip()
        print("Executing code snippet...")
        output, success = execute_code(code_snippet)
        print("Code snippet output:\n", output)

        if success and output.strip():
            context = loop_prompt_success
        else:
            if not output.strip():
                error_message = "No output was produced."
            else:
                error_message = output.split("\n")[-2]
            context = loop_prompt_error.format(error=error_message)
            print("Error:", error_message)
    else:
        context = response

    for _ in range(num_iterations - 1):  # Change the range to `num_iterations - 1` to account for the initial response
        current_prompt = context
        response = ask_davinci(current_prompt, conversation_history)

        if response is None:
            print("AI response is None. Skipping this iteration.")
            continue

        add_to_history("User", current_prompt)
        add_to_history("AI", response)
        print("AI:", response)

        if response.startswith("@CODE-SNIPPET:"):
            code_snippet = response[len("@CODE-SNIPPET:"):].strip()
            print("Executing code snippet...")

            output, success = execute_code(code_snippet)
            print("Code snippet output:\n", output)

            if success and output.strip():
                context = loop_prompt_success
            else:
                if not output.strip():
                    error_message = "No output was produced."
                else:
                    error_message = output.split("\n")[-2]
                context = loop_prompt_error.format(error=error_message)
                print("Error:", error_message)
        else:
            context = response



# ... (The code below this line remains the same)





if __name__ == "__main__":
    use_default = input("Do you want to use the default world context prompt? (yes/no): ").lower()
    if use_default == "no" or use_default == "n":
        world_context_prompt = input("Please enter your custom world context prompt: ")

    override_iterations = input("Do you want to override the default iteration count? (yes/no): ").lower()
    if override_iterations == "yes" or override_iterations == "y":
        num_iterations = int(input("Please enter the custom iteration count: "))

    main_loop(world_context_prompt, loop_prompt_success, loop_prompt_error, num_iterations)
    summary_prompt = config["Prompts"]["summary_prompt"]
    summary_response = ask_davinci(summary_prompt, conversation_history)
    print(f"\nUser Prompt: {summary_prompt}\nAI Response: {summary_response}")
    sys.exit(0)
