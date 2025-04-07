proCoder-project/
├── venv/
├── proCoder/
│   ├── __init__.py
│   ├── main.py         # CLI entry point, main loop, streaming, git prompts
│   ├── config.py       # Load configuration (OpenRouter key, headers, model)
│   ├── ai_client.py    # Handle interaction with OpenRouter API (streaming)
│   ├── file_manager.py # Handle reading/writing local files
│   ├── git_utils.py    # Git operations (check repo, diff, stage, commit)
│   ├── utils.py        # Helper functions (diffing, code extraction, history)
│   └── __main__.py     # Allows running with python -m proCoder
├── .env.example      # Example environment file
├── .gitignore
└── setup.py          # To make it installable
