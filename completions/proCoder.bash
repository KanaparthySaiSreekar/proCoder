# Bash completion for proCoder
# Source this file or add it to ~/.bash_completion.d/

_procoder_completions() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Main commands
    local commands="setup login main models account exec resume completion"

    # Options for specific commands
    case "${prev}" in
        proCoder)
            COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
            return 0
            ;;
        main)
            COMPREPLY=( $(compgen -f -- ${cur}) )
            return 0
            ;;
        exec)
            COMPREPLY=( $(compgen -W "resume" -- ${cur}) )
            return 0
            ;;
        resume)
            COMPREPLY=( $(compgen -W "--last" -- ${cur}) )
            return 0
            ;;
        models)
            COMPREPLY=( $(compgen -W "anthropic openai google meta mistral" -- ${cur}) )
            return 0
            ;;
        completion)
            COMPREPLY=( $(compgen -W "bash zsh fish" -- ${cur}) )
            return 0
            ;;
        *)
            ;;
    esac

    # Global options
    local global_opts="--help --version"
    COMPREPLY=( $(compgen -W "${global_opts}" -- ${cur}) )
}

complete -F _procoder_completions proCoder
