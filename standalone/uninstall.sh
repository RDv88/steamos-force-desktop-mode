#!/bin/sh
set -e

INSTALL_DIR="$HOME/.local/share/force-desktop-mode"
APPS_DIR="$HOME/.local/share/applications"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
LOGOUT_HOOK="$HOME/.config/plasma-workspace/shutdown/force-desktop-mode.sh"

echo "Uninstalling Force Desktop Mode..."

systemctl --user disable --now force-desktop-mode-watch.service 2>/dev/null || true
rm -f "$SYSTEMD_USER_DIR/force-desktop-mode-watch.service"
systemctl --user daemon-reload

rm -f "$LOGOUT_HOOK"
rm -f "$APPS_DIR/force-desktop-mode.desktop"
rm -rf "$INSTALL_DIR"

echo "Done. Your settings are still kept at ~/.config/force-desktop-mode/ in case you reinstall."
echo "Remove that folder too if you want a completely clean uninstall."
