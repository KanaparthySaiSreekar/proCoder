# Fish completion for proCoder
# Install to ~/.config/fish/completions/

# Remove any existing proCoder completions
complete -c proCoder -e

# Main commands
complete -c proCoder -f -n "__fish_use_subcommand" -a "setup" -d "Run interactive setup wizard"
complete -c proCoder -f -n "__fish_use_subcommand" -a "login" -d "Quick login with API key"
complete -c proCoder -f -n "__fish_use_subcommand" -a "main" -d "Start interactive coding session"
complete -c proCoder -f -n "__fish_use_subcommand" -a "models" -d "Browse available AI models"
complete -c proCoder -f -n "__fish_use_subcommand" -a "account" -d "View OpenRouter account information"
complete -c proCoder -f -n "__fish_use_subcommand" -a "exec" -d "Execute non-interactive command"
complete -c proCoder -f -n "__fish_use_subcommand" -a "resume" -d "Resume a previous session"
complete -c proCoder -f -n "__fish_use_subcommand" -a "completion" -d "Generate shell completion scripts"

# Global options
complete -c proCoder -l help -d "Show help message"
complete -c proCoder -l version -d "Show version information"

# Subcommand-specific completions
complete -c proCoder -f -n "__fish_seen_subcommand_from main" -a "(__fish_complete_path)"
complete -c proCoder -f -n "__fish_seen_subcommand_from exec" -a "resume" -d "Resume previous execution"
complete -c proCoder -f -n "__fish_seen_subcommand_from exec" -l last -d "Resume last session"
complete -c proCoder -f -n "__fish_seen_subcommand_from resume" -l last -d "Resume most recent session"
complete -c proCoder -f -n "__fish_seen_subcommand_from models" -a "anthropic openai google meta mistral deepseek" -d "Filter by provider"
complete -c proCoder -f -n "__fish_seen_subcommand_from completion" -a "bash zsh fish" -d "Shell type"
