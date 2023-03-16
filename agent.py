import configparser
import openai
import os
import sys
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
from rich.console import Console
from rich.syntax import Syntax

config = configparser.ConfigParser()
config.read('config.ini')
world_context_prompt = config.get('Prompts', 'world_context_prompt')
loop_prompt_success = config.get('Prompts', 'loop_prompt_success')
loop_prompt_error = config.get('Prompts', 'loop_prompt_error')
num_iterations = config.getint('Settings', 'num_iterations')

openai_api_key = os.environ.get("OPENAI_API_KEY")

if openai_api_key:
    openai.api_key = openai_api_key
else:
    print("Error: OPENAI_API_KEY environment variable not found.")
    sys.exit(1)

conversation_history = []

console = Console()

def add_to_history(role, content):
    message = {"role": role, "content": content}
    conversation_history.append(message)

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

def execute_code(code):
    console.print(f"Executing: {code}")
    with StringIO() as stdout_buffer, StringIO() as stderr_buffer:
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            try:
                exec(code)
                stdout_output = stdout_buffer.getvalue()
                stderr_output = stderr_buffer.getvalue()
                success = True
            except Exception as e:
                stdout_output = stdout_buffer.getvalue()
                stderr_output = f"Error: {str(e)}\n{traceback.format_exc()}"
                success = False

    output = f"STDOUT:\n{stdout_output}\nSTDERR:\n{stderr_output}"
    return output, success

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
    main_loop(world_context_prompt, loop_prompt_success, loop_prompt_error, num_iterations)
    
    summary_prompt = config.get('Prompts', 'summary_prompt')
    summary_response = ask_davinci(summary_prompt, conversation_history)
    add_to_history("User", summary_prompt)
    add_to_history("AI", summary_response)

    console.print(f"User: {summary_prompt}\nAI: {summary_response}")
    sys.exit(0)
