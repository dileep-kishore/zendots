#!/usr/bin/env bash

# Arch Linux Package Installation Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    echo -e "${RED}Error: Do not run this script as root${NC}"
    exit 1
fi

sudo pacman -S --needed base-devel git

# Check if paru is installed
if ! command -v paru &>/dev/null; then
    echo -e "${YELLOW}paru is not installed. Exiting${NC}"
    exit
fi

# Function to check if a package is installed
is_installed() {
    pacman -Qi "$1" &>/dev/null
}

# Function to install package with pacman
install_pacman() {
    local pkg=$1
    if is_installed "$pkg"; then
        echo -e "${GREEN}✓${NC} $pkg is already installed"
    else
        echo -e "${BLUE}→${NC} Installing $pkg with pacman..."
        sudo pacman -S --noconfirm "$pkg"
    fi
}

# Function to install package with paru
install_paru() {
    local pkg=$1
    if is_installed "$pkg"; then
        echo -e "${GREEN}✓${NC} $pkg is already installed"
    else
        echo -e "${BLUE}→${NC} Installing $pkg with paru..."
        paru -S --noconfirm "$pkg"
    fi
}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Installing Official Repository Packages${NC}"
echo -e "${BLUE}========================================${NC}"

# Official repository packages (pacman)
PACMAN_PACKAGES=(
    gnome-keyring
    blueman
    aichat
    aria2
    atuin
    bat
    bc
    btop
    chezmoi
    direnv
    entr
    eza
    fastfetch
    fd
    fzf
    github-cli # gh
    git-delta
    glow
    jq
    just
    lazygit
    lua
    luarocks
    neovim
    nodejs # node
    nvm
    p7zip
    python-pipx # pipx
    uv
    pixi
    ripgrep
    rustup
    python
    go
    starship
    tealdeer
    tmux
    unzip
    yazi
    yq
    zip
    zoxide
    ghostty
    kitty
    ttf-hack-nerd
    ttf-firacode-nerd
    ttf-cascadia-code-nerd
    ttf-lilex-nerd
    ttf-fantasque-nerd
    otf-monaspace
    ttf-monaspace-frozen
    ttf-victor-mono-nerd
    ast-grep
    bat-extras
    biome
    corkscrew
    dua-cli
    git-cliff
    jc
    lazydocker
    ouch
    television
    vivid
    pipx
    brave-bin
    vivaldi
    procs
)

for pkg in "${PACMAN_PACKAGES[@]}"; do
    install_pacman "$pkg"
done

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Installing AUR Packages${NC}"
echo -e "${BLUE}========================================${NC}"

# AUR packages (paru)
AUR_PACKAGES=(
    maplemono-nf-unhinted
    carapace-bin
    git-extras
    oh-my-posh-bin
    rich-cli
    sesh-bin
    tmuxinator
    visual-studio-code-bin
    cursor-bin
    warp-terminal-bin
    opencode-bin
    claude-code
    claude-desktop-native
)

for pkg in "${AUR_PACKAGES[@]}"; do
    install_paru "$pkg"
done

echo -e "${YELLOW}Manual steps required:${NC}"
echo "  1. Initialize rustup: rustup default stable"
echo "  2. Configure atuin: atuin init"
echo "  3. Install Node.js packages globally if needed"
echo "  4. Run 'gh auth login' to authenticate GitHub CLI"
echo "  5. Run the other relevant scripts in this folder"
echo ""

echo -e "${GREEN}Installation complete!${NC}"
echo -e "${YELLOW}Note: Some applications may require a shell restart to function properly.${NC}"
