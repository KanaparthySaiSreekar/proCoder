# proCoder Installation Script for Windows PowerShell
# Usage: irm https://raw.githubusercontent.com/KanaparthySaiSreekar/proCoder/main/install.ps1 | iex

$ErrorActionPreference = "Stop"

$REPO_URL = "git+https://github.com/KanaparthySaiSreekar/proCoder.git"

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  🚀 proCoder AI Assistant Installer" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ $pythonVersion detected" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Python is not installed." -ForegroundColor Red
    Write-Host "Please install Python 3.8 or higher from https://www.python.org/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation." -ForegroundColor Yellow
    exit 1
}

# Check Python version
try {
    $versionString = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    $version = [version]$versionString
    $requiredVersion = [version]"3.8"

    if ($version -lt $requiredVersion) {
        Write-Host "❌ Error: Python 3.8 or higher required (found $versionString)" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "⚠️  Warning: Could not verify Python version" -ForegroundColor Yellow
}

# Check if pipx is available
$usePipx = $false
try {
    pipx --version | Out-Null
    Write-Host "✓ pipx detected - using isolated installation" -ForegroundColor Green
    $usePipx = $true
} catch {
    try {
        pip --version | Out-Null
        Write-Host "✓ pip detected - installing with pip" -ForegroundColor Green
    } catch {
        Write-Host "❌ Error: Neither pipx nor pip found" -ForegroundColor Red
        Write-Host "Please run: python -m ensurepip --upgrade" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "📦 Installing proCoder..." -ForegroundColor Cyan
Write-Host ""

try {
    if ($usePipx) {
        # Install with pipx (isolated environment - recommended)
        $existing = pipx list | Select-String "procoder-ai"
        if ($existing) {
            Write-Host "🔄 Upgrading existing installation..." -ForegroundColor Yellow
            pipx upgrade procoder-ai
        } else {
            pipx install $REPO_URL
        }
    } else {
        # Install with pip (user installation)
        pip install --user --upgrade $REPO_URL

        # Check if Scripts directory is in PATH
        $scriptsPath = python -c "import site; import os; print(os.path.join(site.USER_BASE, 'Scripts'))"
        $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

        if (-not $currentPath.Contains($scriptsPath)) {
            Write-Host ""
            Write-Host "⚠️  Adding Python Scripts directory to PATH..." -ForegroundColor Yellow

            $newPath = "$currentPath;$scriptsPath"
            [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
            $env:Path = "$env:Path;$scriptsPath"

            Write-Host "✓ Added to PATH (you may need to restart your terminal)" -ForegroundColor Green
        }
    }

    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "  ✅ Installation Complete!" -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🎉 proCoder is now installed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Run setup wizard:    proCoder setup" -ForegroundColor White
    Write-Host "  2. Start coding:        proCoder main" -ForegroundColor White
    Write-Host ""
    Write-Host "Quick commands:" -ForegroundColor Cyan
    Write-Host "  proCoder setup          Interactive first-time setup" -ForegroundColor White
    Write-Host "  proCoder login          Quick login with existing key" -ForegroundColor White
    Write-Host "  proCoder main [files]   Start AI coding session" -ForegroundColor White
    Write-Host "  proCoder models         Browse available AI models" -ForegroundColor White
    Write-Host "  proCoder --help         Show all commands" -ForegroundColor White
    Write-Host ""
    Write-Host "Documentation: https://github.com/KanaparthySaiSreekar/proCoder" -ForegroundColor Cyan
    Write-Host ""

    # Test if command is available
    try {
        Get-Command proCoder -ErrorAction Stop | Out-Null
        Write-Host "✓ 'proCoder' command is ready to use" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Command not found. Please restart your PowerShell terminal." -ForegroundColor Yellow
    }

    Write-Host ""

} catch {
    Write-Host ""
    Write-Host "❌ Installation failed: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Make sure Python is in your PATH" -ForegroundColor White
    Write-Host "  2. Try running PowerShell as Administrator" -ForegroundColor White
    Write-Host "  3. Manual install: git clone $REPO_URL && cd proCoder && pip install -e ." -ForegroundColor White
    Write-Host ""
    exit 1
}
