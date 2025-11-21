#!/usr/bin/env bash

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
print_info() {
    echo -e "${GREEN}==>${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}==>${NC} $1"
}

print_error() {
    echo -e "${RED}==>${NC} $1"
}

# Check if running on Arch Linux
if ! command -v pacman &>/dev/null; then
    print_error "This script is designed for Arch Linux (pacman not found)"
    exit 1
fi

# Determine package manager (prefer paru over yay over pacman)
if command -v paru &>/dev/null; then
    PM="paru"
    PM_FLAGS="-S --needed --noconfirm"
elif command -v yay &>/dev/null; then
    PM="yay"
    PM_FLAGS="-S --needed --noconfirm"
else
    PM="sudo pacman"
    PM_FLAGS="-S --needed --noconfirm"
fi

print_info "Using package manager: $PM"

# Core LaTeX packages
CORE_PACKAGES=(
    texlive-basic            # Basic LaTeX distribution
    texlive-bin              # Contains latexmk, xelatex, lualatex, pdflatex
    texlive-binextra         # Contains latexmk, xelatex, lualatex, pdflatex
    texlive-latex            # LaTeX base packages
    texlive-latexrecommended # Recommended LaTeX packages
    texlive-latexextra       # Extra LaTeX packages (beamer, etc.)
    texlive-plaingeneric
)

# Additional useful packages
ADDITIONAL_PACKAGES=(
    texlive-fontsrecommended # Recommended fonts
    texlive-fontsextra       # Extra fonts (many font families)
    texlive-mathscience      # Math and science packages (amsmath, etc.)
    texlive-bibtexextra      # BibTeX/biblatex packages
    texlive-publishers       # Publisher-specific styles (IEEE, ACM, etc.)
    texlive-pictures         # TikZ and other drawing packages
    texlive-xetex            # XeTeX support
    texlive-luatex           # LuaTeX support
)

# Optional packages (large downloads)
OPTIONAL_PACKAGES=(
    texlive-humanities # Humanities packages
    texlive-music      # Music notation packages
    texlive-games      # Game typesetting packages
    biber              # Modern BibTeX replacement for biblatex
)

# Utility packages
UTILITY_PACKAGES=(
    perl-yaml-tiny    # Required by latexindent
    perl-file-homedir # Required by latexindent
)

print_info "Installing core LaTeX packages..."
$PM $PM_FLAGS "${CORE_PACKAGES[@]}"

print_info "Installing additional LaTeX packages..."
$PM $PM_FLAGS "${ADDITIONAL_PACKAGES[@]}"

print_info "Installing utility packages..."
$PM $PM_FLAGS "${UTILITY_PACKAGES[@]}"

# Ask about optional packages
read -p "$(echo -e "${YELLOW}Install optional packages (humanities, music, games, biber)?${NC} [y/N]: ")" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Installing optional packages..."
    $PM $PM_FLAGS "${OPTIONAL_PACKAGES[@]}"
fi

print_info "Updating TeX Live Manager database..."
sudo tlmgr init-usertree 2>/dev/null || true

print_info "Verifying installations..."
echo ""
echo "Checking installed LaTeX tools:"
command -v latex &>/dev/null && echo "   latex:      $(latex --version | head -n1)" || echo "   latex: NOT FOUND"
command -v pdflatex &>/dev/null && echo "   pdflatex:   $(pdflatex --version | head -n1)" || echo "   pdflatex: NOT FOUND"
command -v xelatex &>/dev/null && echo "   xelatex:    $(xelatex --version | head -n1)" || echo "   xelatex: NOT FOUND"
command -v lualatex &>/dev/null && echo "   lualatex:   $(lualatex --version | head -n1)" || echo "   lualatex: NOT FOUND"
command -v latexmk &>/dev/null && echo "   latexmk:    $(latexmk --version | head -n1)" || echo "   latexmk: NOT FOUND"
command -v bibtex &>/dev/null && echo "   bibtex:     $(bibtex --version | head -n1)" || echo "   bibtex: NOT FOUND"
command -v biber &>/dev/null && echo "   biber:      $(biber --version | head -n1)" || echo "   biber: NOT FOUND"

echo ""
print_info "LaTeX installation complete!"
print_info "You can now use: pdflatex, xelatex, lualatex, and latexmk"
echo ""
print_warning "To test your installation, create a simple .tex file and compile it:"
echo "  echo '\\documentclass{article}\\begin{document}Hello World\\end{document}' > test.tex"
echo "  latexmk -pdf test.tex"
