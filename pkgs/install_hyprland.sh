#!/usr/bin/env bash

set -e

# Main dependencies
# NOTE: There is a conflict between wireplumber and pipewire-media-session
# sudo dnf install pipewire wireplumber pavucontrol
sudo dnf install qt5-qtwayland qt6-qtwayland

# Hyprland and related tools
sudo dnf copr enable -y solopasha/hyprland
sudo dnf install \
    hyprland \
    hyprpolkitagent \
    xdg-desktop-portal-hyprland \
    xdg-desktop-portal-gtk \
    hyprland-qt-support \
    hyprcursor \
    hyprpicker \
    hypridle \
    hyprlock \
    hyprsunset \
    hyprshot

# NOTE: You should remove other xdg-desktop-portal-* (except xdg-desktop-portal-gtk)

# Misc tools: bar, wallpaper, clipboard, screenshot
sudo dnf install waybar-git swww wl-clipboard cliphist nwg-clipman
sudo dnf install grim slurp
sudo dnf install network-manager-applet wlogout blueman
sudo dnf install libinput
# Others: copq wl-clip-persist

# Notification: SwayNotificationCenter
sudo dnf copr enable -y erikreider/SwayNotificationCenter
sudo dnf install SwayNotificationCenter

# Launcher: wofi and walker
sudo dnf copr enable -y errornointernet/walker
sudo dnf install wofi walker

# Cursors
sudo dnf copr enable peterwu/rendezvous
sudo dnf install bibata-cursor-themes

# Syncthingtray
sudo dnf config-manager addrepo --from-repofile=https://download.opensuse.org/repositories/home:mkittler/Fedora_42/home:mkittler.repo
sudo dnf install syncthingtray
