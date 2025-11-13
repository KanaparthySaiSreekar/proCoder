#compdef proCoder

# Zsh completion for proCoder
# Install to a directory in your $fpath (e.g., /usr/local/share/zsh/site-functions)

_procoder() {
    local -a commands
    commands=(
        'setup:Run interactive setup wizard'
        'login:Quick login with API key'
        'main:Start interactive coding session'
        'models:Browse available AI models'
        'account:View OpenRouter account information'
        'exec:Execute non-interactive command'
        'resume:Resume a previous session'
        'completion:Generate shell completion scripts'
    )

    local -a global_opts
    global_opts=(
        '--help:Show help message'
        '--version:Show version information'
    )

    _arguments -C \
        '1: :->command' \
        '*::arg:->args' \
        ${global_opts}

    case $state in
        command)
            _describe 'proCoder command' commands
            ;;
        args)
            case $line[1] in
                main)
                    _files
                    ;;
                exec)
                    _arguments \
                        'resume:Resume previous execution' \
                        '--last:Resume last session'
                    ;;
                resume)
                    _arguments \
                        '--last:Resume most recent session'
                    ;;
                models)
                    _arguments \
                        ':provider:(anthropic openai google meta mistral deepseek)'
                    ;;
                completion)
                    _arguments \
                        ':shell:(bash zsh fish)'
                    ;;
            esac
            ;;
    esac
}

_procoder "$@"
