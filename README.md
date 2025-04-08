# proCoder AI Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) <!-- Optional license badge -->
<!-- Add other badges if desired (e.g., build status, code quality) -->

**proCoder** is an interactive AI coding assistant that runs directly in your terminal. Powered by models accessible via [OpenRouter.ai](https://openrouter.ai/), it helps you understand, modify, and generate code by integrating with your local file system and Git workflow.

Ask questions about your code, request refactoring, generate new snippets, get explanations, and apply suggested changes directly to your files after reviewing a diff – all within your terminal environment.

## Features

*   **Interactive Chat:** Conversational interface for coding assistance.
*   **File Context Loading:** Load local code files directly into the conversation context using `/load`.
*   **AI-Powered Code Modification:** Request changes to loaded files.
*   **Diff Preview:** View proposed changes as a `diff` before applying.
*   **User Confirmation:** Changes are only applied to local files after your explicit confirmation (`y/n/d/q` prompt).
*   **Streaming Responses:** AI responses are streamed token-by-token for a more responsive feel.
*   **Git Integration (Optional):**
    *   Detects if running within a Git repository.
    *   Prompts to stage and commit changes after they are applied (configurable via `.env`).
    *   Uses standard Git commands.
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
        *   📄 `file_manager.py` - Manages reading and writing local files
        *   📄 `git_utils.py` - Helper functions for Git commands
        *   📄 `main.py` - Main CLI application logic, commands, chat loop
        *   📄 `utils.py` - Utility functions (diffing, code extraction, etc.)
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
        *   `/clear`: Clear conversation history and loaded files.
        *   `/context`: Show the current context being sent to the AI (for debugging).
        *   `/help`: Show available commands again.
        *   `/quit` or `/exit`: Exit the assistant.

5.  **Apply Changes:**
    *   When the AI proposes changes, review the diff presented.
    *   Type `y` to accept, `n` to reject, `d` to see the full proposed file content, or `q` to stop applying changes for this turn.
    *   If accepted and Git integration is active, you may be prompted to stage and commit.

## Future Improvements & Ideas

*   **Robust Context Management:** Implement token counting (`tiktoken`) and intelligent context truncation/summarization to handle large files and long conversations effectively.
*   **Advanced Code Extraction:** Improve the reliability of extracting code blocks, potentially by prompting the AI for a more structured output format (e.g., JSON containing file changes).
*   **Support for New File Creation:** Allow the AI to create new files based on user requests and extracted code blocks.
*   **Enhanced Git Integration:**
    *   Show `git status` or branch info more proactively.
    *   Option to automatically generate commit messages based on the changes.
    *   Support for diffing against specific commits or branches.
    *   Consider using `GitPython` library for more complex interactions (optional dependency).
*   **Configuration File:** Move more settings (e.g., prompts, model parameters like temperature) to a dedicated config file (e.g., `config.toml`).
*   **Testing:** Add comprehensive unit and integration tests.
*   **Multi-file Awareness:** Develop better strategies for the AI to understand relationships and perform changes across multiple files simultaneously.
*   **Undo Functionality:** Implement a way to revert the last applied file change.
*   **Plugin System:** Allow extending functionality with custom commands or integrations.
*   **Error Handling:** More granular error reporting and recovery for API and file operations.
*   **Windows `pyreadline3`:** Conditionally install and import `pyreadline3` on Windows for better line editing, similar to the built-in `readline` on Unix-like systems.

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
