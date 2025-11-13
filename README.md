# proCoder AI Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.4.0-green.svg)](https://github.com/KanaparthySaiSreekar/proCoder)

**proCoder** is a production-ready AI coding assistant that runs directly in your terminal. Powered by models accessible via [OpenRouter.ai](https://openrouter.ai/), it provides advanced features like file editing, code search, undo/redo, and intelligent context management.

## 🚀 One-Line Install

**macOS/Linux:** `curl -fsSL https://raw.githubusercontent.com/KanaparthySaiSreekar/proCoder/main/install.sh | bash`

**Windows:** `irm https://raw.githubusercontent.com/KanaparthySaiSreekar/proCoder/main/install.ps1 | iex`

**pipx:** `pipx install git+https://github.com/KanaparthySaiSreekar/proCoder.git`

Then run: `proCoder setup` → `proCoder main` 🎉

**What makes proCoder special?**
- 🎯 **Professional-grade file operations** - Create, modify, and track all changes with full undo/redo
- 🔍 **Built-in code search** - Find anything in your codebase without leaving the chat
- 🧠 **Smart context management** - Never exceed token limits with automatic monitoring and warnings
- 🔒 **Safe by default** - Review diffs before applying any changes
- ⚡ **Fast & responsive** - Streaming responses and efficient token usage
- 🔄 **Multi-model switching** - Switch between 12+ AI models on the fly (Claude, GPT-4, Gemini, Llama, etc.)
- 💾 **Persistent memory** - Remembers project facts, preferences, and context across sessions
- 🚀 **Easy setup** - Interactive wizard gets you started in under 2 minutes

## Table of Contents

- [Quick Start](#quick-start)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Examples](#examples)
- [Recent Updates](#recent-updates)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Quick Start

### One-Line Install (Recommended)

**macOS / Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/KanaparthySaiSreekar/proCoder/main/install.sh | bash
```

**Windows PowerShell:**
```powershell
irm https://raw.githubusercontent.com/KanaparthySaiSreekar/proCoder/main/install.ps1 | iex
```

**Using pipx (Cross-platform):**
```bash
pipx install git+https://github.com/KanaparthySaiSreekar/proCoder.git
```

**Using pip (Cross-platform):**
```bash
pip install --user git+https://github.com/KanaparthySaiSreekar/proCoder.git
```

### First Run

After installation, just run:
```bash
proCoder setup    # Interactive setup wizard (< 2 minutes)
proCoder main     # Start coding!
```

### Manual Installation

If you prefer to install from source:
```bash
git clone https://github.com/KanaparthySaiSreekar/proCoder.git
cd proCoder
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -e .
proCoder setup
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
*   **Multi-Model Switching:** Switch between 12+ AI models dynamically with `/model` command (Claude Opus/Sonnet/Haiku, GPT-4/3.5, Gemini Flash/Pro, Llama 3, Mistral, DeepSeek Coder, and more).
*   **Persistent Memory:** Project-level memory system that remembers facts, preferences, architectural notes, and todos across sessions.
*   **Interactive Setup Wizard:** First-time setup opens browser, validates API key, and configures everything automatically.
*   **Model Browser:** Explore 100+ available models with pricing, context limits, and descriptions via `proCoder models`.

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
    *   📄 `.procoder_memory.json` - Persistent project memory (*Git ignored*)
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
        *   📄 `model_manager.py` - Multi-model switching and management (v0.4.0)
        *   📄 `memory_system.py` - Persistent session memory across restarts (v0.4.0)
        *   📄 `openrouter_integration.py` - Setup wizard, login, and model browser (v0.4.0)
        *   📄 `.gitignore` - Specifies intentionally untracked files for Git



## Installation

**TL;DR:** See [Quick Start](#quick-start) for one-line install commands.

### Prerequisites

*   [Python](https://www.python.org/downloads/) 3.8 or higher
*   An [OpenRouter.ai](https://openrouter.ai/) account (free tier available)

### Installation Methods

#### 1. Automated Install Scripts (Recommended)

The easiest way to install proCoder - handles everything automatically:

**macOS / Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/KanaparthySaiSreekar/proCoder/main/install.sh | bash
```

**Windows PowerShell:**
```powershell
irm https://raw.githubusercontent.com/KanaparthySaiSreekar/proCoder/main/install.ps1 | iex
```

#### 2. Using pipx (Isolated Environment)

[pipx](https://pipx.pypa.io/) installs CLI tools in isolated environments - best practice for Python CLI apps:

```bash
# Install pipx if you don't have it
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install proCoder
pipx install git+https://github.com/KanaparthySaiSreekar/proCoder.git
```

#### 3. Using pip (User Install)

Direct installation with pip:

```bash
pip install --user git+https://github.com/KanaparthySaiSreekar/proCoder.git
```

**Note:** Make sure `~/.local/bin` (Linux/macOS) or `%APPDATA%\Python\Scripts` (Windows) is in your PATH.

#### 4. From Source (Development)

For contributing or local development:

```bash
git clone https://github.com/KanaparthySaiSreekar/proCoder.git
cd proCoder
python3 -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -e .
```

### Post-Installation

After installation, run the setup wizard:
```bash
proCoder setup
```

This will:
1. Open your browser to OpenRouter.ai
2. Guide you through API key creation
3. Validate and save your configuration
4. Show your account dashboard

Then start coding:
```bash
proCoder main [your-files...]
```

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
        *   `/model [name|list|back]`: Switch AI model or list available models.
        *   `/or [account|models|help]`: OpenRouter account & model management.
        *   `/remember [show|fact|pref]`: Manage persistent project memory.
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

#### In-Session Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/load <path>...` | Load files into context | `/load src/main.py tests/test.py` |
| `/drop <path>...` | Remove files from context | `/drop tests/test.py` |
| `/files` | List loaded files | `/files` |
| `/model [name\|list\|back]` | Switch AI model | `/model sonnet`, `/model list` |
| `/or [account\|models\|help]` | OpenRouter management | `/or models`, `/or account` |
| `/remember [show\|fact\|pref]` | Persistent memory | `/remember fact framework=FastAPI` |
| `/search <pattern> [glob]` | Search for regex pattern | `/search "def.*test" *.py` |
| `/find <name> [glob]` | Find function/class definitions | `/find MyClass *.py` |
| `/undo` | Undo last file change | `/undo` |
| `/redo` | Redo undone change | `/redo` |
| `/history` | Show change history | `/history` |
| `/clear` | Clear conversation & files | `/clear` |
| `/context` | Debug: show AI context | `/context` |
| `/help` | Show help message | `/help` |
| `/quit` or `/exit` | Exit proCoder | `/quit` |

#### CLI Commands

| Command | Description |
|---------|-------------|
| `proCoder setup` | Interactive setup wizard (first-time setup) |
| `proCoder login` | Quick login for existing users |
| `proCoder main [files...]` | Start interactive coding session |
| `proCoder models [provider]` | Browse all available AI models |
| `proCoder account` | View OpenRouter account info & usage |

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

### Example 6: Switching AI Models (v0.4.0)

```bash
proCoder main src/algorithm.py

>>> /model list                    # See all available models
>>> /model gpt4                    # Switch to GPT-4 for complex reasoning
>>> Optimize this sorting algorithm for performance
>>> /model deepseek                # Switch to DeepSeek Coder for implementation
>>> Implement the optimized version
>>> /model back                    # Return to previous model
```

Choose the best model for each task without restarting.

### Example 7: Using Project Memory (v0.4.0)

```bash
proCoder main

>>> /remember fact framework=FastAPI technology
>>> /remember fact database=PostgreSQL technology
>>> /remember pref code_style=Google
>>> /remember arch API "RESTful design with async endpoints"

# Later, or in a new session:
>>> /remember show
# AI now knows your project uses FastAPI + PostgreSQL and prefers Google style

>>> Create a new database model for users
# AI automatically applies your preferences and architectural patterns
```

Build up project knowledge that persists across sessions.

### Example 8: Easy First-Time Setup (v0.4.0)

```bash
# Brand new installation
proCoder setup

# Interactive wizard:
# 1. Opens browser to openrouter.ai/keys
# 2. You create/copy your API key
# 3. Paste key (validated automatically)
# 4. Shows your account credits & usage
# 5. Ready to code!

proCoder main    # Start coding immediately
```

From zero to coding in under 2 minutes.

## Recent Updates

### Version 0.4.0 - Professional-Grade Features (Latest)

Version 0.4.0 adds sophisticated multi-model management and persistent memory capabilities, making proCoder competitive with enterprise tools like Claude Code and Cursor CLI.

**🔄 Multi-Model Switching**
- Switch between 12+ AI models on the fly without restarting
- Support for Anthropic (Claude 3 Opus/Sonnet/Haiku), OpenAI (GPT-4/3.5 Turbo), Google (Gemini Flash/Pro), Meta (Llama 3), Mistral, DeepSeek Coder, and more
- Smart model aliases: `/model opus`, `/model gpt4`, `/model gemini`
- Partial name matching: `/model sonnet` automatically finds `claude-3-sonnet`
- Model comparison table with speed, cost, context window, and best use cases
- Model history: `/model back` to switch to previous model

**💾 Persistent Memory System**
- Remembers project facts, user preferences, and architectural decisions across sessions
- Store information in categories: facts, preferences, patterns, architecture, todos
- Memory stored in `.procoder_memory.json` at git repo root
- Commands:
  - `/remember fact framework=FastAPI technology` - Store project facts
  - `/remember pref indent=4` - Save user preferences
  - `/remember pattern <description>` - Record recurring patterns
  - `/remember arch <component> <description>` - Document architecture
  - `/remember show [section]` - View stored memory
- Automatic context injection: AI sees relevant memory in every conversation
- Export and clear capabilities for memory management

**🚀 Easy Setup & Login**
- Interactive setup wizard: `proCoder setup`
  - Opens browser to OpenRouter.ai
  - Validates API key automatically
  - Saves to `.env` file
  - Shows account dashboard
- Quick login for existing users: `proCoder login`
- Account management: `proCoder account` - View credits, usage, rate limits
- Model browser: `proCoder models [provider]` - Explore 100+ models with pricing
- In-session OpenRouter commands via `/or`

| Feature | v0.3.0 | v0.4.0 |
|---------|--------|--------|
| **Model Switching** | ❌ Manual .env edit required | ✅ Dynamic switching with `/model` |
| **Model Selection** | ⚠️ One model per session | ✅ 12+ models, switch anytime |
| **Persistent Memory** | ❌ None | ✅ Facts, preferences, architecture, todos |
| **Setup Experience** | ⚠️ Manual .env configuration | ✅ Interactive wizard with browser |
| **Account Management** | ❌ None | ✅ Dashboard with usage & credits |
| **Model Discovery** | ❌ Check OpenRouter website | ✅ Built-in browser with filtering |

### Version 0.3.0 - Advanced Coding Features

Version 0.3.0 transformed proCoder from a basic CLI agent into a production-ready coding assistant with advanced features comparable to commercial tools.

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
# Solution 1: Use the interactive setup wizard (easiest)
proCoder setup

# Solution 2: Quick login if you have a key
proCoder login

# Solution 3: Manual setup
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
1. Try a faster model (v0.4.0): /model gemini or /model haiku
2. Reduce context by loading fewer files
3. Check your internet connection
4. Verify OpenRouter API status at https://status.openrouter.ai
```

**Issue: Model switching not working (v0.4.0)**
```bash
# Check available models
>>> /model list

# Use exact key or alias
>>> /model sonnet          # ✓ Correct
>>> /model claude-sonnet   # ✓ Also works (partial match)
>>> /model Claude          # ✗ Won't work (too generic)

# View current model
>>> /model info
```

**Issue: Memory not persisting (v0.4.0)**
```bash
# Check if memory file exists
ls .procoder_memory.json

# Memory is stored in git repo root, or current directory if not in a repo
# Verify you're in the same directory/repo

# View memory
>>> /remember show

# If memory file is corrupted, you can delete and start fresh
rm .procoder_memory.json
```

**Issue: Setup wizard won't open browser (v0.4.0)**
```bash
# Manual steps:
1. Visit https://openrouter.ai/keys in your browser
2. Create an account and API key
3. Run: proCoder login
4. Paste your key when prompted
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

**New in v0.4.0:** Switch models dynamically with `/model <name>` command!

| Model Key | Full ID | Speed | Cost | Best For |
|-----------|---------|-------|------|----------|
| `gemini-flash` | `google/gemini-flash-1.5` | ⚡⚡⚡ | Free | General use, large contexts (1M tokens) |
| `sonnet` | `anthropic/claude-3.5-sonnet` | ⚡⚡ | $$ | Balanced performance, coding |
| `opus` | `anthropic/claude-3-opus` | ⚡ | $$$ | Complex reasoning, long analysis |
| `haiku` | `anthropic/claude-3-haiku` | ⚡⚡⚡ | $ | Fast responses |
| `gpt4` | `openai/gpt-4` | ⚡ | $$$ | Highest quality |
| `gpt-4-turbo` | `openai/gpt-4-turbo` | ⚡⚡ | $$ | Long documents (128K) |
| `deepseek` | `deepseek/deepseek-coder` | ⚡⚡ | $ | Code generation & refactoring |
| `llama` | `meta-llama/llama-3-70b` | ⚡⚡ | $ | Open source alternative |

**Quick Switching:**
```bash
>>> /model gemini        # Start with free Gemini Flash
>>> /model gpt4          # Switch to GPT-4 for complex task
>>> /model deepseek      # Use DeepSeek for code generation
>>> /model list          # See all 12+ available models
>>> /model back          # Return to previous model
```

Or browse all 100+ models: `proCoder models` or `/or models`

Check [OpenRouter Models](https://openrouter.ai/models) for the complete list and real-time pricing.

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
