#!/usr/bin/env bash
# Apply the Mac Mini's non-default macOS settings to this Mac.
# Values were read from macmini on 2026-10-22; re-read the same keys there
# with `defaults read <domain> <key>` before changing one here.

set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "defaults.sh: macOS only" >&2
    exit 1
fi

write() {
    defaults write "$@"
    echo "set $1 $2"
}

write NSGlobalDomain AppleInterfaceStyle -string Dark
write NSGlobalDomain AppleScrollerPagingBehavior -int 1
write NSGlobalDomain NSAllowContinuousSpellChecking -bool false
write NSGlobalDomain NSGlassDiffusionSetting -int 1
write NSGlobalDomain SLSMenuBarUseBlurredAppearance -int 1
write NSGlobalDomain com.apple.mouse.scaling -float 1
write NSGlobalDomain com.apple.scrollwheel.scaling -float 0.5

write com.apple.dock autohide -bool true
write com.apple.dock magnification -bool true
write com.apple.dock largesize -int 73
# OmniWM and its app rules expect Spaces to keep their order.
write com.apple.dock mru-spaces -bool false
write com.apple.dock expose-group-apps -bool true
write com.apple.dock wvous-tl-corner -int 2 # Mission Control
write com.apple.dock wvous-tl-modifier -int 0
write com.apple.dock wvous-tr-corner -int 12 # Notification Center
write com.apple.dock wvous-tr-modifier -int 0
write com.apple.dock wvous-bl-corner -int 3 # Application windows
write com.apple.dock wvous-bl-modifier -int 0
write com.apple.dock wvous-br-corner -int 4 # Desktop
write com.apple.dock wvous-br-modifier -int 0

write com.apple.finder NewWindowTarget -string PfAF
write com.apple.finder ShowPathbar -bool true
write com.apple.finder ShowStatusBar -bool true
write com.apple.finder ShowExternalHardDrivesOnDesktop -bool true

# Stage Manager must stay off for OmniWM (docs/omniwm.md).
write com.apple.WindowManager GloballyEnabled -bool false
write com.apple.WindowManager EnableTiledWindowMargins -bool false
write com.apple.WindowManager EnableStandardClickToShowDesktop -bool false

killall Dock Finder SystemUIServer 2>/dev/null || true
echo "Done. Log out and back in for the appearance and scrolling settings."
