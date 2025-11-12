# proCoder AI Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.3.0-green.svg)](https://github.com/KanaparthySaiSreekar/proCoder)

**proCoder** is a production-ready AI coding assistant that runs directly in your terminal. Powered by models accessible via [OpenRouter.ai](https://openrouter.ai/), it provides advanced features like file editing, code search, undo/redo, and intelligent context management.

**What makes proCoder special?**
- 🎯 **Professional-grade file operations** - Create, modify, and track all changes with full undo/redo
- 🔍 **Built-in code search** - Find anything in your codebase without leaving the chat
- 🧠 **Smart context management** - Never exceed token limits with automatic monitoring and warnings
- 🔒 **Safe by default** - Review diffs before applying any changes
- ⚡ **Fast & responsive** - Streaming responses and efficient token usage

## Table of Contents

- [Quick Start](#quick-start)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Examples](#examples)
- [Recent Updates](#recent-updates-v030)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/KanaparthySaiSreekar/proCoder.git
cd proCoder
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# 2. Install
pip install -e .

# 3. Configure (add your OpenRouter API key)
cp .env.example .env
# Edit .env and add: OPENROUTER_API_KEY="sk-or-v1-..."

# 4. Start coding!
proCoder main path/to/your/code.py
```

## Features

### Core Capabilities
*   **Interactive Chat:** Conversational interface for coding assistance.
*   **File Context Loading:** Load local code files directly into the conversation context using `/load`.
*   **AI-Powered Code Modification:** Request changes to loaded files.
*   **New File Creation:** AI can create new files in your project with approval.
*   **Diff Preview:** View proposed changes as a `diff` before applying.
*   **User Confirmation:** Changes are only applied to local files after your explicit confirmation (`y/n/d/q` prompt).
*   **Streaming Responses:** AI responses are streamed token-by-token for a more responsive feel.

### Advanced Features
*   **Code Search & Grep:** Built-in `/search` command for finding patterns in your codebase (regex supported).
*   **Definition Finder:** `/find` command to locate function and class definitions across files.
*   **Undo/Redo:** Full undo/redo support for all file changes with `/undo` and `/redo`.
*   **Change History:** Track all modifications with `/history` command.
*   **Token Counting:** Accurate token counting using `tiktoken` with automatic context management.
*   **Smart Context Management:** Automatic warning and truncation when approaching model token limits.

### Git Integration (Optional)
*   Detects if running within a Git repository.
*   Prompts to stage and commit changes after they are applied (configurable via `.env`).
*   Uses standard Git commands.

### Configuration
*   **Configurable AI Model:** Choose any compatible model available on [OpenRouter.ai](https://openrouter.ai/) via the `.env` file.
*   **OpenRouter Integration:** Leverages the OpenRouter API for access to a wide variety of LLMs.
*   **Basic Command History:** Uses `readline` (on Linux/macOS) for command history within the session.

## Project Structure

*   📁 **proCoder-project/** *(Root Directory)*
    *   📄 `.env` - Local environment variables (API Key, secrets - *Git ignored*)
    *   📄 `.env.example` - Example environment file template
    *   📄 `README.md` - This documentation file
    *   📄 `setup.py` - Package metadata and installation script
    *   📄 `requirements.txt` - *(Optional)* List of dependencies
    *   📁 `venv/` - Virtual environment directory (*Git ignored*)
    *   📁 **proCoder/** *(Main Python package source code)*
        *   📄 `__init__.py` - Makes 'proCoder' importable as a package
        *   📄 `__main__.py` - Enables running via `python -m proCoder`
        *   📄 `ai_client.py` - Handles communication with the OpenRouter API
        *   📄 `config.py` - Loads configuration from `.env` and defaults
        *   📄 `file_manager.py` - Manages reading, writing, and undo/redo for files
        *   📄 `git_utils.py` - Helper functions for Git commands
        *   📄 `main.py` - Main CLI application logic, commands, chat loop
        *   📄 `utils.py` - Utility functions (diffing, code extraction, etc.)
        *   📄 `search_utils.py` - Code search and grep functionality
        *   📄 `token_counter.py` - Token counting and context management
        *   📄 `.gitignore` - Specifies intentionally untracked files for Git



## Installation

**Prerequisites:**

*   [Python](https://www.python.org/downloads/) 3.8+
*   [Git](https://git-scm.com/downloads/)
*   An [OpenRouter.ai](https://openrouter.ai/) account and API Key.

**Steps:**

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/[your-username]/proCoder-project.git
    cd proCoder-project
    ```

2.  **Create and Activate Virtual Environment:**
    *   **Linux/macOS:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    *   **Windows (Command Prompt/PowerShell):**
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```

3.  **Install Dependencies:**
    This command uses `setup.py` to install the project and its requirements in editable mode (`-e`), meaning changes you make to the source code will be reflected immediately when you run the tool.
    ```bash
    pip install -e .
    ```
    *(Ensure you are in the `proCoder-project` root directory containing `setup.py` when running this.)*

4.  **Configure API Key:**
    *   Rename the example environment file:
        *   Linux/macOS: `cp .env.example .env`
        *   Windows: `copy .env.example .env`
    *   Open the `.env` file in a text editor.
    *   Paste your OpenRouter API key: `OPENROUTER_API_KEY="sk-or-v1-..."`
    *   (Optional) Customize `AI_MODEL_NAME` (check [OpenRouter Models](https://openrouter.ai/models) for options), `GIT_AUTO_STAGE`, `GIT_AUTO_COMMIT`, `YOUR_SITE_URL`, `YOUR_SITE_NAME`.

## Usage

1.  **Activate Virtual Environment:** (If not already active)
    ```bash
    # Linux/macOS: source venv/bin/activate
    # Windows: .\venv\Scripts\activate
    ```

2.  **Run the Assistant:**
    Start the interactive session by running the `main` command:
    ```bash
    proCoder main
    ```

3.  **Load Files (Optional):**
    You can load files when starting:
    ```bash
    proCoder main path/to/your/file.py another/file.js
    ```
    Or load them during the session using the `/load` command:
    ```
    >>> /load src/my_module.py data/config.json
    ```

4.  **Interact:**
    *   Ask coding questions, request refactoring, generate code, etc.
    *   Use commands within the chat:
        *   `/load <path>...`: Load or reload file(s) into context.
        *   `/drop <path>...`: Remove file(s) from context.
        *   `/files`: List currently loaded files.
        *   `/search <pattern> [files]`: Search for pattern in files (regex supported).
        *   `/find <identifier> [files]`: Find definitions of functions/classes.
        *   `/undo`: Undo the last file change.
        *   `/redo`: Redo the last undone change.
        *   `/history`: Show change history.
        *   `/clear`: Clear conversation history and loaded files.
        *   `/context`: Show the current context being sent to the AI (for debugging).
        *   `/help`: Show available commands again.
        *   `/quit` or `/exit`: Exit the assistant.

### Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `/load <path>...` | Load files into context | `/load src/main.py tests/test.py` |
| `/drop <path>...` | Remove files from context | `/drop tests/test.py` |
| `/files` | List loaded files | `/files` |
| `/search <pattern> [glob]` | Search for regex pattern | `/search "def.*test" *.py` |
| `/find <name> [glob]` | Find function/class definitions | `/find MyClass *.py` |
| `/undo` | Undo last file change | `/undo` |
| `/redo` | Redo undone change | `/redo` |
| `/history` | Show change history | `/history` |
| `/clear` | Clear conversation & files | `/clear` |
| `/context` | Debug: show AI context | `/context` |
| `/help` | Show help message | `/help` |
| `/quit` or `/exit` | Exit proCoder | `/quit` |

5.  **Search & Find:**
    ```
    >>> /search "def process" *.py
    >>> /find MyClass *.py
    ```

6.  **Apply Changes:**
    *   When the AI proposes changes, review the diff presented.
    *   Type `y` to accept, `n` to reject, `d` to see the full proposed file content, or `q` to stop applying changes for this turn.
    *   If accepted and Git integration is active, you may be prompted to stage and commit.
    *   Use `/undo` to revert changes if needed.

## Examples

### Example 1: Refactoring Code

```bash
proCoder main src/utils.py

>>> Can you refactor the parse_data function to be more pythonic?
```

The AI will:
1. Analyze the current code
2. Suggest improvements
3. Show you a diff of the changes
4. Apply changes only after your approval

### Example 2: Creating New Features

```bash
proCoder main src/app.py

>>> Add a new file src/validators.py with email and phone validation functions
```

The AI will:
1. Generate the new file content
2. Show you the complete file for review
3. Create the file after you approve
4. Automatically load it into context

### Example 3: Finding Code

```bash
proCoder main

>>> /search "class.*Database" *.py
>>> /find authenticate *.py
```

Quickly locate patterns or definitions without leaving the assistant.

### Example 4: Safe Experimentation

```bash
>>> Rewrite this function to use async/await

# Review changes, then:
>>> /history           # See what changed
>>> /undo              # Revert if needed
>>> /redo              # Reapply if you change your mind
```

### Example 5: Working with Large Projects

```bash
proCoder main src/models.py src/views.py src/controllers.py

>>> How do these three files interact? Can you optimize the data flow?
```

The AI will understand the context across all loaded files and suggest coordinated changes.

## Recent Updates (v0.3.0)

### What's New

Version 0.3.0 is a major upgrade that transforms proCoder from a basic CLI agent into a production-ready coding assistant with advanced features comparable to commercial tools.

| Feature | v0.2.0 | v0.3.0 |
|---------|--------|--------|
| **File Creation** | ❌ Not supported | ✅ Full support with preview & approval |
| **Code Search** | ❌ None | ✅ Regex search + definition finder |
| **Token Counting** | ⚠️ Approximate (8K hardcoded) | ✅ Accurate with tiktoken, model-specific |
| **Context Management** | ⚠️ Basic message truncation | ✅ Smart limits + auto-truncation |
| **Undo/Redo** | ❌ None (.bak files only) | ✅ Full history (50 operations) |
| **Change Tracking** | ❌ None | ✅ Timestamps, file lists, status |
| **Safety** | ⚠️ Could exceed token limits | ✅ Warnings + automatic protection |

### New Features Details

**🎯 New File Creation**
- AI can propose and create new files in your project
- Full content preview before creation
- Automatic loading into context
- Undo support for created files

**🔍 Code Search & Grep**
- `/search <pattern> [files]` - Regex-based code search
- `/find <identifier> [files]` - Locate function/class definitions
- Smart binary file detection
- Context lines around matches
- Exclusion of common directories (.git, node_modules, etc.)

**🧠 Token Counting & Context Management**
- Accurate counting with `tiktoken` library
- Support for all major models (GPT-4, Claude, Gemini, etc.)
- Real-time usage display with color-coded warnings
- Automatic truncation when approaching limits
- Preserves system prompts during truncation

**⏮️ Undo/Redo Functionality**
- `/undo` - Revert the last file operation
- `/redo` - Reapply undone changes
- `/history` - View complete change history
- Tracks up to 50 operations with timestamps
- Works for both modifications and file creation

## Troubleshooting

### Common Issues

**Issue: "OPENROUTER_API_KEY not found"**
```bash
# Solution: Make sure .env file exists and contains your API key
cp .env.example .env
# Edit .env and add: OPENROUTER_API_KEY="sk-or-v1-..."
```

**Issue: "tiktoken not installed" warning**
```bash
# Solution: Reinstall with all dependencies
pip install -e .
# Or install tiktoken separately
pip install tiktoken
```

**Issue: Token limit warnings**
```bash
# Solutions:
1. Use /clear to start fresh conversation
2. /drop files you don't need anymore
3. Load fewer files at once
4. The assistant will auto-truncate if severely over limit
```

**Issue: Changes not appearing in files**
```bash
# Check:
1. Did you approve the changes? (type 'y' when prompted)
2. Check file permissions
3. Use /history to see if changes were recorded
4. Try /undo then /redo to reapply
```

**Issue: Readline/command history not working (Linux/macOS)**
```bash
# Install readline development headers
# Ubuntu/Debian:
sudo apt-get install libreadline-dev
# macOS: Usually included, try reinstalling Python
```

**Issue: Model responses are slow or timing out**
```bash
# Solutions:
1. Try a faster model (e.g., gemini-flash-1.5)
2. Reduce context by loading fewer files
3. Check your internet connection
4. Verify OpenRouter API status
```

### Debug Mode

To see more detailed information:
```bash
# Check context being sent to AI
>>> /context

# View token usage and limits
# (Automatically displayed before each AI call)

# Check what files are loaded
>>> /files

# View complete change history
>>> /history
```

### Getting Help

If you encounter issues:
1. Check the [Issues](https://github.com/KanaparthySaiSreekar/proCoder/issues) page
2. Review the troubleshooting section above
3. Open a new issue with:
   - Your Python version (`python --version`)
   - Your OS
   - Complete error message
   - Steps to reproduce

## Dependencies

proCoder uses the following key libraries:

| Library | Version | Purpose |
|---------|---------|---------|
| `openai` | ≥1.10.0 | OpenRouter API communication |
| `tiktoken` | ≥0.5.0 | Accurate token counting |
| `rich` | ≥13.0.0 | Beautiful terminal UI |
| `typer` | ≥0.9.0 | CLI framework |
| `python-dotenv` | ≥1.0.0 | Environment configuration |

All dependencies are automatically installed when you run `pip install -e .`

## Configuration Options

Edit your `.env` file to customize proCoder:

```bash
# Required
OPENROUTER_API_KEY="sk-or-v1-..."

# Optional - Model Selection
AI_MODEL_NAME="google/gemini-flash-1.5"  # Fast and free
# Other options:
# "anthropic/claude-3-sonnet"
# "openai/gpt-4"
# "meta-llama/llama-3-70b"

# Optional - Git Integration
GIT_AUTO_STAGE=false    # Auto-stage changes
GIT_AUTO_COMMIT=false   # Auto-commit changes

# Optional - OpenRouter Tracking
YOUR_SITE_URL="https://your-site.com"
YOUR_SITE_NAME="Your App Name"
```

### Recommended Models

| Model | Speed | Cost | Best For |
|-------|-------|------|----------|
| `google/gemini-flash-1.5` | ⚡⚡⚡ | Free | General use, large contexts |
| `anthropic/claude-3-sonnet` | ⚡⚡ | $$ | Complex reasoning |
| `openai/gpt-4` | ⚡ | $$$ | Highest quality |
| `meta-llama/llama-3-70b` | ⚡⚡ | $ | Open source |

Check [OpenRouter Models](https://openrouter.ai/models) for the complete list and pricing.

## Future Improvements & Ideas

*   **Advanced Code Extraction:** Improve the reliability of extracting code blocks with structured output (e.g., JSON)
*   **Enhanced Git Integration:** Auto-generate commit messages, diff against specific commits
*   **Async API Calls:** Implement async/await for better performance
*   **Context Summarization:** Intelligent summarization for very long conversations
*   **Configuration File:** Move settings to `config.toml`
*   **Testing:** Add comprehensive unit and integration tests
*   **Multi-file Refactoring:** Better strategies for coordinated changes
*   **Plugin System:** Custom commands and integrations
*   **Windows Support:** Better `pyreadline3` integration

## Contributing

Contributions are welcome! Please feel free to open an issue or submit a pull request.

1.  Fork the repository.
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details (if you create one).

---

*Created by Kanaparthy Sai Sreekar kanapasai@gmail.com*
