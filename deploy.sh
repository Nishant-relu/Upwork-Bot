#!/usr/bin/env bash
# =============================================================================
# Upwork Bot — Deployment Script
# Usage: bash deploy.sh
# Run as the ubuntu user (not root). sudo access required.
# =============================================================================

set -euo pipefail

# ── colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── config ────────────────────────────────────────────────────────────────────
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
PYTHON="$VENV_DIR/bin/python3"
PIP="$VENV_DIR/bin/pip"
PATCHRIGHT="$VENV_DIR/bin/patchright"
SERVICE_SRC="$PROJECT_DIR/services/bot_scheduler.service"
XVFB_SERVICE="/etc/systemd/system/xvfb.service"
BOT_SERVICE="/etc/systemd/system/bot_scheduler.service"
DISPLAY_NUM=":1"

echo ""
echo "============================================================"
echo "  Upwork Bot — Deployment"
echo "  Project: $PROJECT_DIR"
echo "============================================================"
echo ""

# ── 0. Pre-flight checks ──────────────────────────────────────────────────────
info "Running pre-flight checks..."

[[ "$EUID" -eq 0 ]] && error "Do not run as root. Run as the ubuntu user (sudo access required)."
command -v sudo >/dev/null || error "sudo not found."

if [[ ! -f "$PROJECT_DIR/.env" ]]; then
    warn ".env file not found at $PROJECT_DIR/.env"
    warn "Create it before starting the bot service. Continuing..."
fi

if [[ ! -f "$PROJECT_DIR/upwork-bot-service-account.json" ]]; then
    warn "Google service account JSON not found at $PROJECT_DIR/upwork-bot-service-account.json"
    warn "The bot will fail to connect to Google Sheets without it. Continuing..."
fi

success "Pre-flight checks passed."
echo ""

# ── 1. System packages ────────────────────────────────────────────────────────
info "Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y \
    xvfb \
    libxi6 libxtst6 libxrandr2 libxss1 \
    libatk1.0-0 libatk-bridge2.0-0 libgtk-3-0 \
    libasound2t64 libcups2 libnss3 libxcomposite1 libxdamage1 \
    wget curl fonts-liberation xdg-utils \
    python3-pip python3-venv \
    -qq 2>&1 | tail -3
success "System dependencies installed."
echo ""

# ── 2. Google Chrome ──────────────────────────────────────────────────────────
if command -v google-chrome &>/dev/null; then
    CHROME_VER=$(google-chrome --version)
    success "Google Chrome already installed: $CHROME_VER"
else
    info "Installing Google Chrome..."
    TMP_DEB="/tmp/google-chrome-stable.deb"
    wget -q "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb" -O "$TMP_DEB"
    sudo dpkg -i "$TMP_DEB" 2>&1 || true
    sudo apt-get install -f -y -qq 2>&1 | tail -3
    rm -f "$TMP_DEB"
    success "Google Chrome installed: $(google-chrome --version)"
fi
echo ""

# ── 3. Python virtual environment ─────────────────────────────────────────────
if [[ -d "$VENV_DIR" ]]; then
    success "Virtual environment already exists at $VENV_DIR"
else
    info "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    success "Virtual environment created."
fi

info "Installing Python requirements..."
"$PIP" install --upgrade pip -q
"$PIP" install -r "$PROJECT_DIR/requirements.txt" -q
"$PIP" install python-xlib -q   # required by pynput X11 backend
success "Python requirements installed."
echo ""

# ── 4. Patchright browser ─────────────────────────────────────────────────────
info "Checking patchright browser driver..."
# patchright stores its driver under the venv; reinstall is idempotent
"$PATCHRIGHT" install chrome 2>&1 | tail -5
success "Patchright browser driver ready."
echo ""

# ── 5. DISPLAY env in .bashrc ─────────────────────────────────────────────────
BASHRC="$HOME/.bashrc"
if grep -q "export DISPLAY=$DISPLAY_NUM" "$BASHRC" 2>/dev/null; then
    success "DISPLAY=$DISPLAY_NUM already set in $BASHRC"
else
    info "Adding DISPLAY=$DISPLAY_NUM to $BASHRC..."
    echo "export DISPLAY=$DISPLAY_NUM" >> "$BASHRC"
    success "Added DISPLAY=$DISPLAY_NUM to $BASHRC"
fi
export DISPLAY="$DISPLAY_NUM"
echo ""

# ── 6. Xvfb systemd service ───────────────────────────────────────────────────
info "Setting up Xvfb systemd service..."
sudo tee "$XVFB_SERVICE" > /dev/null << EOF
[Unit]
Description=X Virtual Frame Buffer
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/Xvfb $DISPLAY_NUM -screen 0 1920x1080x24 -ac +extension GLX +render -noreset
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable xvfb.service
sudo systemctl restart xvfb.service
sleep 2

if systemctl is-active --quiet xvfb.service; then
    success "Xvfb service is running on DISPLAY $DISPLAY_NUM"
else
    error "Xvfb service failed to start. Check: journalctl -u xvfb.service"
fi
echo ""

# ── 7. Verify pynput works on the virtual display ────────────────────────────
info "Verifying pynput on DISPLAY $DISPLAY_NUM..."
DISPLAY="$DISPLAY_NUM" "$PYTHON" -c "
from pynput.mouse import Controller
m = Controller()
m.move(1, 1)
print('pynput mouse OK')
from pynput.keyboard import Controller as KCtrl
KCtrl()
print('pynput keyboard OK')
" && success "pynput works correctly on virtual display." || warn "pynput check failed — review DISPLAY and Xvfb."
echo ""

# ── 8. Update bot_scheduler.service with correct paths ───────────────────────
info "Writing bot_scheduler.service..."
cat > "$SERVICE_SRC" << EOF
[Unit]
Description=Bot Scheduler Service
After=network.target xvfb.service
Requires=xvfb.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PYTHON $PROJECT_DIR/bot_scheduler.py
ExecStop=$PYTHON $PROJECT_DIR/stop_bot.py
EnvironmentFile=$PROJECT_DIR/.env
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1
Environment=DISPLAY=$DISPLAY_NUM

[Install]
WantedBy=multi-user.target
EOF

sudo cp "$SERVICE_SRC" "$BOT_SERVICE"
sudo systemctl daemon-reload
sudo systemctl enable bot_scheduler.service
success "bot_scheduler.service installed and enabled."
echo ""

# ── 9. Summary ────────────────────────────────────────────────────────────────
echo "============================================================"
echo -e "${GREEN}  Deployment complete!${NC}"
echo "============================================================"
echo ""
echo "  Google Chrome : $(google-chrome --version)"
echo "  Python        : $($PYTHON --version)"
echo "  Xvfb          : $(systemctl is-active xvfb.service)"
echo "  Bot service   : $(systemctl is-active bot_scheduler.service 2>/dev/null || echo 'stopped (not started yet)')"
echo ""
echo "  Commands:"
echo "    Start bot  →  sudo systemctl start bot_scheduler"
echo "    Stop bot   →  sudo systemctl stop bot_scheduler"
echo "    Live logs  →  journalctl -u bot_scheduler -f"
echo "    Status     →  sudo systemctl status bot_scheduler"
echo ""
echo "  NOTE: Run 'source ~/.bashrc' or open a new terminal"
echo "        for DISPLAY=$DISPLAY_NUM to take effect in your shell."
echo ""
