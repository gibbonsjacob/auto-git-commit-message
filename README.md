# Auto Git Commit Message Generator with LLM

This project automatically generates Git commit messages based on staged changes using an LLM (Large Language Model) via Ollama.

---

## Features

* Reads staged changes in a Git repository.
* Processes multiple files at once.
* Filters out distracting files (e.g., `pyproject.toml`, `uv.lock`) and appends notes for documentation updates.
* Generates a concise commit message using the LLM.
* Copies the generated message to the clipboard.

---

## Requirements

* Python 3.12 (recommended)
* Zsh (for convenience functions)
* Ollama installed and accessible via your `$PATH`
* Ollama LLM model I used: `hf.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF:Q4_K_M`

### Installing Ollama

If you do not have Ollama installed, you can download it here: [https://ollama.com/download](https://ollama.com/download)

After installing, make sure you can run the following in a terminal:

```bash
ollama --version
```

---

## Important Note

**The Ollama server must already be running** for this tool to work. Start it with:

```bash
ollama serve
```

Do not try to start the server from the Python script. The script assumes a running server.

---

## Setup

1. Clone this repository.

```bash
git clone https://github.com/gibbonsjacob/auto-git-commit-message.git
cd auto_commit_message
```

2. Create a Python virtual environment and install dependencies.

```bash
uv init
uv venv 
source .venv/bin/activate
uv pip install -r pyproject.toml
uv sync --all-groups
```

3. Ensure Ollama is running with `ollama serve`.

4. Source the Zsh function (optional, for convenience) to your ~/.zshrc file.

```bash
echo 'source ./auto_commit_message/make_commit_message.zsh' >> ~/.zshrc
```

---

## Usage

### Using Python Directly

```bash
REPO_ROOT="$HOME/path/to/auto_commit_message"
git diff --staged | "$REPO_ROOT/.venv/bin/python3.12" "$REPO_ROOT/auto_commit_message/git_diff_llm.py"
```

### Using the Zsh Function

Once sourced, simply run:

```bash
make-commit-message
```

The generated commit message will be printed and copied to your clipboard.

---

## File Structure

```
auto_commit_message/
├── git_diff_llm.py   # Main script for generating commit messages
├── server_utils.py   # Utility functions (if needed in future, currently not for starting server)
├── make_commit_message.zsh  # Zsh function for convenience
├── .venv/                # Python virtual environment
├── README.md
├── pyproject.toml
└── uv.lock
```

---

## Notes

* The script currently filters out `pyproject.toml` and `uv.lock` files to avoid them dominating the commit message.
* The LLM is designed to focus on code changes, not documentation or config files, but will append "and updated documentation" if filtered files are detected.
* The generated message is concise, imperative, and under 128 characters if possible.

---

## Troubleshooting

* **Server not running error:** Make sure you have `ollama serve` running in a terminal before executing the script.
* **Python environment issues:** Ensure the virtual environment is activated.
* **Clipboard issues:** The script uses `pbcopy` on macOS. Modify `copy_to_clipboard` in `git_diff_llm.py` if using Linux (`xclip`) or Windows.

---

## License

MIT License
