#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Get the root directory of the project (parent of scripts directory)
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Change to project root directory
cd "$PROJECT_ROOT" || exit 1

echo "🎀 Setting up Charm tools from $(pwd)..."

install_go_debian_ubuntu() {
    echo "📦 Installing Go on Debian/Ubuntu..."
    sudo apt update
    # Add the latest Go repository
    sudo add-apt-repository -y ppa:longsleep/golang-backports
    sudo apt update
    sudo apt install -y golang-go
}

install_go_redhat_centos() {
    echo "📦 Installing Go on RHEL/CentOS..."
    # Check RHEL/CentOS version
    if [ -f "/etc/os-release" ]; then
        . /etc/os-release
        if [[ "${VERSION_ID}" == "7" ]]; then
            # CentOS/RHEL 7
            sudo yum install -y epel-release
            sudo yum install -y golang
        else
            # CentOS/RHEL 8 or later
            sudo dnf install -y epel-release
            sudo dnf install -y golang
        fi
    else
        sudo yum install -y golang
    fi
}

# Check if Go is installed
if ! command -v go &> /dev/null; then
    echo "❌ Go is not installed."
    read -p "Would you like to install Go now? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📦 Installing Go..."
        
        # Detect OS and distribution
        if [ -f "/etc/os-release" ]; then
            . /etc/os-release
            case ${ID} in
                "ubuntu"|"debian")
                    install_go_debian_ubuntu
                    ;;
                "rhel"|"centos"|"rocky"|"almalinux")
                    install_go_redhat_centos
                    ;;
                *)
                    echo "❌ Unsupported Linux distribution: ${ID}"
                    echo "Please install Go manually."
                    exit 1
                    ;;
            esac
        else
            echo "❌ Cannot determine Linux distribution."
            echo "Please install Go manually."
            exit 1
        fi

        # Verify Go installation
        if command -v go &> /dev/null; then
            echo "✅ Go installed successfully"
            # Setup GOPATH if it doesn't exist
            if [ ! -d "$HOME/go" ]; then
                mkdir -p "$HOME/go"
            fi
        else
            echo "❌ Go installation failed"
            exit 1
        fi
    else
        echo "❌ Go is required. Please install Go and try again."
        exit 1
    fi
fi

# Show Go version
GO_VERSION=$(go version)
echo "ℹ️  Using Go version: $GO_VERSION"

# Install Charm tools
echo "📦 Installing Charm tools..."

# Create temporary directory for installations
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR" || exit

# Install Gum
echo "🍬 Installing Gum..."
go install github.com/charmbracelet/gum@latest

# Install Bubble Tea examples (removing this as it's causing errors and isn't necessary)
# echo "🫧 Installing Bubble Tea examples..."
# go install github.com/charmbracelet/bubbletea/examples/...@latest

# Install Soft Serve (fixing the package path)
echo "🍦 Installing Soft Serve..."
go install github.com/charmbracelet/soft-serve/cmd/soft@latest

# Install Charm (the main CLI tool)
echo "✨ Installing Charm..."
go install github.com/charmbracelet/charm@latest

# Cleanup
cd - || exit
rm -rf "$TEMP_DIR"

# Function to update PATH and GOPATH in current session
update_current_path() {
    # Update PATH and GOPATH in current session
    export PATH="$PATH:$HOME/go/bin"
    export GOPATH="$HOME/go"
}

# Add Go bin to PATH if not already present
if [[ ":$PATH:" != *":$HOME/go/bin:"* ]]; then
    echo "📝 Adding Go bin to PATH..."
    
    # Update current session first
    update_current_path
    
    # Detect current shell
    CURRENT_SHELL=$(basename "$SHELL")
    echo "🔍 Detected shell: $CURRENT_SHELL"
    
    case "$CURRENT_SHELL" in
        "bash")
            SHELL_RC="$HOME/.bashrc"
            echo "📝 Updating .bashrc..."
            echo 'export PATH=$PATH:$HOME/go/bin' >> "$SHELL_RC"
            echo 'export GOPATH=$HOME/go' >> "$SHELL_RC"
            echo "✅ Updated .bashrc"
            ;;
        "zsh")
            SHELL_RC="$HOME/.zshrc"
            echo "📝 Updating .zshrc..."
            echo 'export PATH=$PATH:$HOME/go/bin' >> "$SHELL_RC"
            echo 'export GOPATH=$HOME/go' >> "$SHELL_RC"
            echo "✅ Updated .zshrc"
            ;;
        *)
            echo "⚠️  Unknown shell: $CURRENT_SHELL"
            echo "📝 Adding to both .bashrc and .zshrc to be safe..."
            echo 'export PATH=$PATH:$HOME/go/bin' >> ~/.bashrc
            echo 'export PATH=$PATH:$HOME/go/bin' >> ~/.zshrc
            echo 'export GOPATH=$HOME/go' >> ~/.bashrc
            echo 'export GOPATH=$HOME/go' >> ~/.zshrc
            ;;
    esac

    # Verify PATH update
    if [[ ":$PATH:" == *":$HOME/go/bin:"* ]]; then
        echo "✅ PATH updated successfully for current session"
    else
        echo "❌ PATH update failed for current session"
        exit 1
    fi
fi

# Rest of the verification code will now work because PATH is updated in current session
echo "✨ Charm tools setup complete!"

# Verify installations after PATH update
echo "✨ Verifying installations..."
if command -v gum &> /dev/null; then
    echo "✅ Gum installed successfully"
    GUM_VERSION=$(gum --version)
    echo "   Version: $GUM_VERSION"
else
    echo "❌ Gum installation failed"
    echo "Installation path: $HOME/go/bin/gum"
    ls -l "$HOME/go/bin/gum" 2>/dev/null || echo "Binary not found!"
fi

if command -v charm &> /dev/null; then
    echo "✅ Charm installed successfully"
    CHARM_VERSION=$(charm --version)
    echo "   Version: $CHARM_VERSION"
else
    echo "❌ Charm installation failed"
    echo "Installation path: $HOME/go/bin/charm"
    ls -l "$HOME/go/bin/charm" 2>/dev/null || echo "Binary not found!"
fi

if command -v soft &> /dev/null; then
    echo "✅ Soft Serve installed successfully"
    SOFT_VERSION=$(soft --version)
    echo "   Version: $SOFT_VERSION"
else
    echo "❌ Soft Serve installation failed"
    echo "Installation path: $HOME/go/bin/soft"
    ls -l "$HOME/go/bin/soft" 2>/dev/null || echo "Binary not found!"
fi

# Provide instructions for future terminal sessions
echo "
✨ Installation complete! Changes are active in current session.

💡 For future terminal sessions, the changes will be loaded automatically.
   If needed, you can manually reload using:
   source ~/.bashrc  # for bash
   source ~/.zshrc   # for zsh
" 