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

PACMAN_PACKAGES=(
    niri
    wofi
    fuzzel
    swaync
    waybar
    xdg-desktop-portal-gtk
    xdg-desktop-portal-gnome
    swww
    hypridle
    hyprlock
    swayidle
    swaylock
    xwayland-satellite
    wl-clipboard
    cliphist
    wl-clip-persist
    libinput
    network-manager-applet
    pavucontrol
    playerctl
    pipewire
    hyprpicker
    swayosd
    proton-vpn-gtk-app
    papirus-icon-theme
    nwg-look
)

AUR_PACKAGES=(
    bibata-cursor-theme
    rose-pine-gtk-theme-full
    ant-dracula-theme-git
    ant-dracula-kvantum-theme-git
    ant-dracula-kde-theme-git
    wlogout
    wlr-which-key-git
    ulauncher
    vicinae-bin
    polycat
)

for pkg in "${PACMAN_PACKAGES[@]}"; do
    install_pacman "$pkg"
done

for pkg in "${AUR_PACKAGES[@]}"; do
    install_paru "$pkg"
done
