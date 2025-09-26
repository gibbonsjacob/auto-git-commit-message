

from langchain_core.runnables import Runnable
from langchain_ollama import ChatOllama
from langchain.schema import HumanMessage, SystemMessage
from typing import Union, Optional, Dict, Any
from server_utils import OllamaServer
import argparse
import re
import subprocess
import psutil 



self_query_retriever_sys_prompt = """


You are an expert assistant that focuses entirely on reading git diff's and generating high-quality Git commit messages from them.

**Your task:** Summarize staged code changes into a concise git commit messages.

**Guidelines:**

* If multiple files/functions have changed, you must give a summary of changes for EACH file/function. 
* You MUST start each file/function's summary with the name of the file/function 
* Always use the imperative mood (e.g., "Add", "Fix", "Update", "Refactor").
* Be concise: ideally under 128 characters for the subject line.
* Focus on intent (the "why" and "what"), not line-by-line details.
* Avoid noise such as file paths, code snippets, or formatting.
* If multiple related changes exist, summarize them into one clear message.
* Do not include explanations, markdown, or anything other than the commit message.


### Examples

**Diff:**

```diff
- def calculate_total(price, tax):
-     return price + price * tax
+ def calculate_total(price, tax_rate):
+     return price + price * tax_rate
```

**Commit message:**
Renamed tax parameter to tax_rate for clarity in the calculate_total function

---

**Diff:**

```diff
+ import logging
+ logging.basicConfig(level=logging.DEBUG)
```

**Commit message:**
Added basic debug logging setup

---

**Diff:**

```diff
- SELECT * FROM users
+ SELECT id, name, email FROM users WHERE active = TRUE
```

**Commit message:**
Refactored query from users table to only return active users with a subset of fields selected

"""





def is_ollama_running(model_name):
    """
    Summary:
        Checks if an Ollama model process is currently running.
    Args:
        model_name (str): Name of the Ollama model.
    
    Returns:
        int | None: PID of the running process if found, otherwise None.
    """
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'ollama' in proc.info['name'] and model_name in ' '.join(proc.info['cmdline']):
                return proc.info['pid']
        except Exception:
            continue
    return None


def split_diff_by_file(diff_text):
    """
    Summary:
        Splits a git diff into a dictionary keyed by filename.
    Args:
        diff_text (str): The full git diff text.
    
    Returns:
        dict: Dictionary mapping filenames to their individual diff text.
    """
    
    file_diffs = {}
    current_file = None
    lines = []

    for line in diff_text.splitlines():
        if line.startswith("diff --git"):
            # Save previous file's diff
            if current_file and lines:
                file_diffs[current_file] = "\n".join(lines)
            # Extract filename (second path in diff header)
            parts = line.split(" ")
            if len(parts) >= 3:
                # diff --git a/file b/file
                current_file = parts[2][2:]  # remove 'b/' prefix
            lines = [line]
        else:
            lines.append(line)

    # Add last file diff
    if current_file and lines:
        file_diffs[current_file] = "\n".join(lines)

    return file_diffs


def preprocess_diff(diff_text, distracting_files=None):
    """
    Summary:
        Removes distracting files from the git diff and returns filtered text.
    Args:
        diff_text (str): The full git diff text.
        distracting_files (list[str], optional): List of filenames to remove. Defaults to ["pyproject.toml", "uv.lock"].
    
    Returns:
        tuple[str, bool]: Filtered diff text and a flag indicating if distracting files were present.
    """
    
    if distracting_files is None:
        distracting_files = ["pyproject.toml", "uv.lock"]

    file_diffs = split_diff_by_file(diff_text)
    append_note = False

    # Here we remove documentation files from the git diff and simply add "and updated documentation" to the end of our commit message
    filtered_file_diffs = {}
    for filename, file_diff in file_diffs.items():
        if filename in distracting_files:
            append_note = True
        else:
            filtered_file_diffs[filename] = file_diff

    filtered_diff_text = "\n".join(filtered_file_diffs.values())
    return filtered_diff_text, append_note



class HelperLLM(Runnable):
    def __init__(self, model_name: str, temperature: float = 0.0):
        self.llm = ChatOllama(model=model_name, temperature=temperature)

    def generate(self, prompt: str) -> str:
        """
        Summary:
            Generates a commit message based on the given diff text.
        Args:
            diff_text (str): The git diff text to generate a message from.
        
        Returns:
            str: Suggested commit message.
        """
        messages = [
            SystemMessage(content=self_query_retriever_sys_prompt),
            HumanMessage(content=prompt),
        ]
        response = self.llm.invoke(messages)
        
        return response.content

    def invoke(
        self,
        input: Union[str, Dict[str, Any]],
        config: Optional[Dict[str, Any]] = None,
    ) -> str:
        if isinstance(input, dict):
            prompt = input.get("text") or input.get("query") or ""
        else:
            prompt = input
            
        if not isinstance(prompt, str):
            prompt = str(prompt)
        return self.generate(prompt)
    

def copy_to_clipboard(text: str):
    """
    Summary:
        Copies the provided text to the macOS clipboard.
    Args:
        text (str): Text to copy.
    
    """
    
    process = subprocess.Popen(
        ['pbcopy'], stdin=subprocess.PIPE, close_fds=True
    )
    process.communicate(input=text.encode('utf-8'))





def generate_commit_message(server: OllamaServer, llm: HelperLLM, diff_text, model_name: str):

    """
    Summary:
        Generates a commit message using the LLM from the given git diff.
        Handles distracting files, Ollama model startup, and regex cleanup.
    Args:
        llm (helperLLM): LLM instance to generate commit messages.
        diff_text (str): Full git diff text.
        model_name (str, optional): Ollama model name. Defaults to "Meta-LLaMA-3.1-8B-Instruct".
    
    Returns:
        str: Generated commit message.
    """

    pid = None
    pid = server.get_pid()
    try:

        
            filtered_diff_text, append_note = preprocess_diff(diff_text)
            response = llm.generate(filtered_diff_text)
            if append_note:
                response += " and updated documentation accordingly"        
        
        # LLM likes to sometimes add "**Commit Message**" to the response, so we'll parse that out here
            return re.sub(r'^\s*\*\*Commit Message:\*\*\s*', '', response, flags=re.IGNORECASE)

    
    finally:
        # If we started Ollama, kill it
        if pid:
            print(f"Killing Ollama process {pid}")
            server.stop()





if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a commit message from staged git diff")
    parser.add_argument("--diff", type=str, help="Optional path to file with git diff (defaults to stdin)")
    args = parser.parse_args()

    model_name = "hf.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF:Q4_K_M"
    server = OllamaServer(model_name)
    server.start()
    if args.diff:
        with open(args.diff, "r") as f:
            diff_text = f.read()
    else:
        import sys
        diff_text = sys.stdin.read()

    if not diff_text.strip():
        print("No diff provided!")
        exit(1)
    
    llm = HelperLLM(model_name=model_name)

    commit_msg = generate_commit_message(server, llm, diff_text, model_name)

    
    print(f"Generated Commit Message: {commit_msg}")
    copy_to_clipboard(commit_msg)
    server.stop()