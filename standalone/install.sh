#!/bin/sh
set -e

REPO="RDv88/steamos-force-desktop-mode"
INSTALL_DIR="$HOME/.local/share/force-desktop-mode"
APPS_DIR="$HOME/.local/share/applications"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

echo "Force Desktop Mode installer"

TAG=$(curl -fsSL "https://api.github.com/repos/$REPO/releases" \
  | grep -m1 '"tag_name"' \
  | sed -E 's/.*"tag_name": *"([^"]+)".*/\1/')

if [ -z "$TAG" ]; then
  echo "Could not determine the latest release, aborting." >&2
  exit 1
fi

echo "Installing version $TAG..."

mkdir -p "$INSTALL_DIR" "$APPS_DIR" "$SYSTEMD_USER_DIR"

RAW_BASE="https://raw.githubusercontent.com/$REPO/$TAG/standalone"

curl -fsSL "$RAW_BASE/force_desktop_mode.py" -o "$INSTALL_DIR/force_desktop_mode.py"
chmod +x "$INSTALL_DIR/force_desktop_mode.py"

curl -fsSL "$RAW_BASE/force-desktop-mode-watch.service" -o "$SYSTEMD_USER_DIR/force-desktop-mode-watch.service"

curl -fsSL "$RAW_BASE/force-desktop-mode.desktop.template" \
  | sed "s|__INSTALL_DIR__|$INSTALL_DIR|g" > "$APPS_DIR/force-desktop-mode.desktop"

systemctl --user daemon-reload

python3 - "$INSTALL_DIR" "$TAG" <<'PYEOF'
import sys

sys.path.insert(0, sys.argv[1])
import force_desktop_mode as fdm

tag = sys.argv[2]
settings = fdm.load_settings()
settings["installed_version"] = tag
fdm.save_settings(settings)

desired = settings["desired_default"]
fdm.sync_logout_hook(desired)
fdm.set_default(desired)
fdm.set_watch_enabled(settings.get("autofix_enabled", True))
PYEOF

echo ""
echo "Installed version $TAG."
echo "Find 'Force Desktop Mode' in your application menu."
