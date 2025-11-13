#!/bin/bash
# proCoder Installation Script for Unix/Linux/macOS
# Usage: curl -fsSL https://raw.githubusercontent.com/KanaparthySaiSreekar/proCoder/main/install.sh | bash

set -e

REPO_URL="https://github.com/KanaparthySaiSreekar/proCoder.git"
INSTALL_DIR="$HOME/.procoder"
BIN_DIR="$HOME/.local/bin"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🚀 proCoder AI Assistant Installer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if Python 3.8+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed."
    echo "Please install Python 3.8 or higher from https://www.python.org/"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Error: Python $REQUIRED_VERSION or higher required (found $PYTHON_VERSION)"
    exit 1
fi

echo "✓ Python $PYTHON_VERSION detected"

# Check if pipx is available, if not check for pip
if command -v pipx &> /dev/null; then
    echo "✓ pipx detected - using isolated installation"
    USE_PIPX=true
elif command -v pip3 &> /dev/null; then
    echo "✓ pip detected - installing with pip"
    USE_PIPX=false
else
    echo "❌ Error: Neither pipx nor pip found"
    echo "Please install pip: python3 -m ensurepip --upgrade"
    exit 1
fi

echo ""
echo "📦 Installing proCoder..."
echo ""

if [ "$USE_PIPX" = true ]; then
    # Install with pipx (isolated environment - recommended)
    if pipx list | grep -q "procoder-ai"; then
        echo "🔄 Upgrading existing installation..."
        pipx upgrade procoder-ai || {
            echo "⚠️  Upgrade failed, reinstalling..."
            pipx uninstall procoder-ai
            pipx install git+${REPO_URL}
        }
    else
        pipx install git+${REPO_URL}
    fi
else
    # Install with pip (user installation)
    pip3 install --user --upgrade git+${REPO_URL}

    # Ensure ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo ""
        echo "⚠️  Adding ~/.local/bin to PATH..."

        # Detect shell and add to appropriate config file
        if [ -n "$BASH_VERSION" ]; then
            SHELL_CONFIG="$HOME/.bashrc"
        elif [ -n "$ZSH_VERSION" ]; then
            SHELL_CONFIG="$HOME/.zshrc"
        else
            SHELL_CONFIG="$HOME/.profile"
        fi

        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_CONFIG"
        export PATH="$HOME/.local/bin:$PATH"

        echo "✓ Added to $SHELL_CONFIG (restart your terminal or run: source $SHELL_CONFIG)"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Installation Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎉 proCoder is now installed!"
echo ""
echo "Next steps:"
echo "  1. Run setup wizard:    proCoder setup"
echo "  2. Start coding:        proCoder main"
echo ""
echo "Quick commands:"
echo "  proCoder setup          Interactive first-time setup"
echo "  proCoder login          Quick login with existing key"
echo "  proCoder main [files]   Start AI coding session"
echo "  proCoder models         Browse available AI models"
echo "  proCoder --help         Show all commands"
echo ""
echo "Documentation: https://github.com/KanaparthySaiSreekar/proCoder"
echo ""

# Test if command is available
if command -v proCoder &> /dev/null; then
    echo "✓ 'proCoder' command is ready to use"
else
    echo "⚠️  Command not found in PATH. You may need to restart your terminal."
    if [ "$USE_PIPX" = false ]; then
        echo "   Or run: source $SHELL_CONFIG"
    fi
fi

echo ""
