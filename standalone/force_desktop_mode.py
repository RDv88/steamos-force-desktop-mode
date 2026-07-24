#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request

REPO = "RDv88/steamos-force-desktop-mode"

CONFIG_DIR = os.path.expanduser("~/.config/force-desktop-mode")
SETTINGS_PATH = os.path.join(CONFIG_DIR, "settings.json")
DEFAULT_SETTINGS = {"autofix_enabled": True, "desired_default": "desktop", "installed_version": None}

LOGOUT_HOOK_DIR = os.path.expanduser("~/.config/plasma-workspace/shutdown")
LOGOUT_HOOK_PATH = os.path.join(LOGOUT_HOOK_DIR, "force-desktop-mode.sh")
LOGOUT_HOOK_CONTENT = """#!/bin/sh
if [ "$(steamosctl get-default-login-mode)" = "desktop" ]; then
    steamosctl switch-to-game-mode
fi
"""

LOGIN_MODE_LABELS = {"desktop": "Desktop Mode (Plasma)", "game": "Game Mode (gamescope)"}

WATCH_SERVICE = "force-desktop-mode-watch.service"
CHECK_INTERVAL_SECONDS = 60

INSTALL_DIR = os.path.expanduser("~/.local/share/force-desktop-mode")
DESKTOP_ENTRY_PATH = os.path.expanduser("~/.local/share/applications/force-desktop-mode.desktop")
SYSTEMD_USER_DIR = os.path.expanduser("~/.config/systemd/user")
APP_ICON = "preferences-desktop"


def load_settings() -> dict:
    try:
        with open(SETTINGS_PATH) as f:
            loaded = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        loaded = {}
    return {**DEFAULT_SETTINGS, **loaded}


def save_settings(settings: dict) -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2)


def run(*args: str) -> tuple:
    try:
        proc = subprocess.run(args, capture_output=True, text=True)
        return proc.returncode, proc.stdout.strip()
    except FileNotFoundError:
        return 127, ""


def kdialog(*args: str) -> tuple:
    return run("kdialog", "--title", "Force Desktop Mode", "--icon", APP_ICON, *args)


def get_current_default():
    code, output = run("steamosctl", "get-default-login-mode")
    return output if code == 0 and output else None


def set_default(mode: str) -> bool:
    code, _ = run("steamosctl", "set-default-login-mode", mode)
    return code == 0


def switch_now(mode: str) -> bool:
    code, _ = run("steamosctl", f"switch-to-{mode}-mode")
    return code == 0


def apply_fix(mode: str) -> bool:
    return set_default(mode) and switch_now(mode)


def sync_logout_hook(desired_default: str) -> None:
    if desired_default == "desktop":
        install_logout_hook()
    else:
        remove_logout_hook()


def install_logout_hook() -> None:
    os.makedirs(LOGOUT_HOOK_DIR, exist_ok=True)
    with open(LOGOUT_HOOK_PATH, "w") as f:
        f.write(LOGOUT_HOOK_CONTENT)
    os.chmod(LOGOUT_HOOK_PATH, 0o755)


def remove_logout_hook() -> None:
    if os.path.exists(LOGOUT_HOOK_PATH):
        os.remove(LOGOUT_HOOK_PATH)


def set_watch_enabled(enabled: bool) -> None:
    action = "enable" if enabled else "disable"
    subprocess.run(["systemctl", "--user", action, "--now", WATCH_SERVICE], capture_output=True)


def uninstall() -> None:
    code, _ = kdialog(
        "--warningyesno",
        "This removes Force Desktop Mode: the app, its menu entry, the auto-heal service, "
        "and the logout hook.\n\nYour current Desktop/Game Mode default is left as-is.\n\n"
        "Uninstall now?",
    )
    if code != 0:
        return

    subprocess.run(["systemctl", "--user", "disable", "--now", WATCH_SERVICE], capture_output=True)
    service_path = os.path.join(SYSTEMD_USER_DIR, WATCH_SERVICE)
    if os.path.exists(service_path):
        os.remove(service_path)
    subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)

    remove_logout_hook()

    if os.path.exists(DESKTOP_ENTRY_PATH):
        os.remove(DESKTOP_ENTRY_PATH)

    kdialog("--msgbox", "Force Desktop Mode has been uninstalled.")

    shutil.rmtree(INSTALL_DIR, ignore_errors=True)
    sys.exit(0)


# ---- Update check (only run from the interactive menu, never from --watch) ----

def latest_release_tag():
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/releases",
            headers={"Accept": "application/vnd.github+json"},
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            releases = json.load(resp)
        tag = releases[0]["tag_name"]
        return tag if re.fullmatch(r"[A-Za-z0-9._-]+", tag) else None
    except Exception:
        return None


def check_for_update(settings: dict) -> None:
    latest = latest_release_tag()
    installed = settings.get("installed_version")
    if not latest or not installed or latest == installed:
        return

    code, _ = kdialog("--yesno", f"An update is available: {latest} (you have {installed}).\n\nUpdate now?")
    if code != 0:
        return

    install_url = f"https://raw.githubusercontent.com/{REPO}/{latest}/standalone/install.sh"
    result = subprocess.run(f"curl -fsSL {install_url} | sh", shell=True)
    if result.returncode == 0:
        kdialog("--msgbox", f"Updated to {latest}. Please reopen Force Desktop Mode.")
    else:
        kdialog("--msgbox", "Update failed. Check your internet connection and try again later.")
    sys.exit(0)


def check_for_update_manual(settings: dict) -> None:
    latest = latest_release_tag()
    installed = settings.get("installed_version")
    if not latest:
        kdialog("--msgbox", "Could not check for updates right now (no internet?).")
        return
    if latest == installed:
        kdialog("--msgbox", f"You're already on the latest version ({installed}).")
        return
    check_for_update(settings)


# ---- Interactive menu ----

def show_menu() -> None:
    settings = load_settings()
    desired = settings["desired_default"]
    current = get_current_default()
    matches = current == desired
    autofix = settings.get("autofix_enabled", True)

    status_icon = "✅" if matches else "⚠️"
    current_label = LOGIN_MODE_LABELS.get(current, current) if current else "unknown"
    desired_label = LOGIN_MODE_LABELS.get(desired, desired)
    status_text = f"{status_icon} Desired: {desired_label}\nCurrent: {current_label}"

    options = [
        "desktop", "Set Desktop Mode as default",
        "game", "Set Game Mode as default",
        "reapply", "Reapply now",
        "autofix", f"Turn auto-heal {'off' if autofix else 'on'} (currently {'on' if autofix else 'off'})",
        "update", "Check for updates",
        "uninstall", "Uninstall Force Desktop Mode",
    ]
    code, choice = kdialog("--menu", status_text, *options)
    if code != 0 or not choice:
        return

    if choice in ("desktop", "game"):
        settings["desired_default"] = choice
        save_settings(settings)
        sync_logout_hook(choice)
        ok = apply_fix(choice)
        label = LOGIN_MODE_LABELS[choice]
        kdialog("--msgbox", f"{label} is now the default." if ok else f"Failed to set {label}, check steamosctl.")
    elif choice == "reapply":
        ok = apply_fix(desired)
        kdialog("--msgbox", "Reapplied successfully." if ok else "Reapply failed, check steamosctl.")
    elif choice == "autofix":
        settings["autofix_enabled"] = not autofix
        save_settings(settings)
        set_watch_enabled(settings["autofix_enabled"])
    elif choice == "update":
        check_for_update_manual(settings)
    elif choice == "uninstall":
        uninstall()

    show_menu()


def watch_loop() -> None:
    while True:
        settings = load_settings()
        if settings.get("autofix_enabled", True):
            current = get_current_default()
            desired = settings["desired_default"]
            if current != desired:
                apply_fix(desired)
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--watch":
        watch_loop()
    else:
        settings = load_settings()
        check_for_update(settings)
        show_menu()
