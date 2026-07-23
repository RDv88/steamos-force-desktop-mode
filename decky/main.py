import asyncio
import json
import os
import pwd
from datetime import datetime, timezone

import decky

CHECK_INTERVAL_SECONDS = 60

LOGIN_MODE_LABELS = {"desktop": "Desktop Mode (Plasma)", "game": "Game Mode (gamescope)"}

# Mirrors the SteamOS "Return to Gaming Mode" desktop entry's own logic: if the persistent
# default is desktop, a plain logout would otherwise just autologin back into desktop, so this
# does a transient switch to game mode first instead.
LOGOUT_HOOK_DIR = os.path.join(decky.DECKY_USER_HOME, ".config", "plasma-workspace", "shutdown")
LOGOUT_HOOK_PATH = os.path.join(LOGOUT_HOOK_DIR, "steamos-force-desktop-mode.sh")
LOGOUT_HOOK_CONTENT = """#!/bin/sh
if [ "$(steamosctl get-default-login-mode)" = "desktop" ]; then
    steamosctl switch-to-game-mode
fi
"""

DEFAULT_SETTINGS = {"autofix_enabled": True, "desired_default": "desktop"}


def _settings_path() -> str:
    return os.path.join(decky.DECKY_PLUGIN_SETTINGS_DIR, "settings.json")


def _load_settings() -> dict:
    try:
        with open(_settings_path(), "r") as f:
            loaded = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        loaded = {}
    return {**DEFAULT_SETTINGS, **loaded}


def _save_settings(settings: dict) -> None:
    os.makedirs(decky.DECKY_PLUGIN_SETTINGS_DIR, exist_ok=True)
    with open(_settings_path(), "w") as f:
        json.dump(settings, f, indent=2)


class Plugin:
    async def _main(self):
        self.settings = _load_settings()
        self.last_action = None
        self.last_action_time = None
        self.last_checked_time = None
        self._task = None

        await self._set_default(self.settings["desired_default"])
        self._sync_logout_hook()

        self._task = asyncio.get_event_loop().create_task(self._watch_loop())
        decky.logger.info("steamos-force-desktop-mode loaded")

    async def _unload(self):
        if self._task:
            self._task.cancel()
        decky.logger.info("steamos-force-desktop-mode unloaded")

    async def _uninstall(self):
        self._remove_logout_hook()
        decky.logger.info("logout hook removed, plugin fully uninstalled")

    # ---- Callables exposed to frontend ----

    async def get_status(self) -> dict:
        return await self._status_dict()

    async def refresh_status(self) -> dict:
        return await self._status_dict()

    async def force_fix(self) -> dict:
        await self._apply_fix(self.settings["desired_default"], reason="manual")
        return await self._status_dict()

    async def set_desired_default(self, mode: str) -> dict:
        if mode not in LOGIN_MODE_LABELS:
            raise ValueError(f"unknown mode: {mode}")
        self.settings["desired_default"] = mode
        _save_settings(self.settings)
        self._sync_logout_hook()
        await self._apply_fix(mode, reason="default changed")
        return await self._status_dict()

    async def set_autofix(self, enabled: bool) -> dict:
        self.settings["autofix_enabled"] = enabled
        _save_settings(self.settings)
        return await self._status_dict()

    # ---- Internal logic ----

    async def _status_dict(self) -> dict:
        current = await self._get_current_default()
        desired = self.settings["desired_default"]
        self.last_checked_time = datetime.now(timezone.utc).isoformat()
        return {
            "session_raw": current,
            "desired_default": desired,
            "matches_desired": current == desired,
            "autofix_enabled": self.settings.get("autofix_enabled", True),
            "last_action": self.last_action,
            "last_action_time": self.last_action_time,
            "last_checked_time": self.last_checked_time,
        }

    async def _get_current_default(self) -> str | None:
        code, output = await self._run("steamosctl", "get-default-login-mode")
        return output if code == 0 and output else None

    async def _set_default(self, mode: str) -> bool:
        code, _ = await self._run("steamosctl", "set-default-login-mode", mode)
        return code == 0

    async def _switch_now(self, mode: str) -> bool:
        code, _ = await self._run("steamosctl", f"switch-to-{mode}-mode")
        return code == 0

    async def _watch_loop(self):
        while True:
            try:
                if self.settings.get("autofix_enabled", True):
                    desired = self.settings["desired_default"]
                    current = await self._get_current_default()
                    if current != desired:
                        await self._apply_fix(desired, reason="auto-heal")
            except Exception as e:
                decky.logger.error(f"error in watch loop: {e}")
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)

    async def _apply_fix(self, mode: str, reason: str):
        set_ok = await self._set_default(mode)
        switch_ok = await self._switch_now(mode)
        self.last_action_time = datetime.now(timezone.utc).isoformat()
        label = LOGIN_MODE_LABELS[mode]
        if set_ok and switch_ok:
            self.last_action = f"set default to {label} ({reason})"
            decky.logger.info(self.last_action)
        else:
            self.last_action = f"failed to set default to {label} ({reason})"
            decky.logger.warning(self.last_action)
        await decky.emit("status_update", await self._status_dict())

    def _sync_logout_hook(self):
        if self.settings["desired_default"] == "desktop":
            self._install_logout_hook()
        else:
            self._remove_logout_hook()

    def _install_logout_hook(self):
        try:
            os.makedirs(LOGOUT_HOOK_DIR, exist_ok=True)
            with open(LOGOUT_HOOK_PATH, "w") as f:
                f.write(LOGOUT_HOOK_CONTENT)
            os.chmod(LOGOUT_HOOK_PATH, 0o755)
            pw = pwd.getpwnam(decky.DECKY_USER)
            os.chown(LOGOUT_HOOK_DIR, pw.pw_uid, pw.pw_gid)
            os.chown(LOGOUT_HOOK_PATH, pw.pw_uid, pw.pw_gid)
            decky.logger.info("logout hook installed")
        except (OSError, KeyError) as e:
            decky.logger.warning(f"could not install logout hook: {e}")

    def _remove_logout_hook(self):
        try:
            if os.path.exists(LOGOUT_HOOK_PATH):
                os.remove(LOGOUT_HOOK_PATH)
        except OSError as e:
            decky.logger.warning(f"could not remove logout hook: {e}")

    async def _run(self, *args: str) -> tuple[int | None, str]:
        # Decky Loader's bundled Python sets LD_LIBRARY_PATH for its own libs; leaking that into
        # system binaries makes them load the wrong shared libs and crash with symbol errors.
        env = os.environ.copy()
        env.pop("LD_LIBRARY_PATH", None)
        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            stdout, stderr = await proc.communicate()
            stdout_text = stdout.decode().strip()
            if proc.returncode != 0:
                output = stderr.decode().strip() or stdout_text
                decky.logger.warning(f"{' '.join(args)} exited with code {proc.returncode}: {output}")
            return proc.returncode, stdout_text
        except FileNotFoundError:
            decky.logger.warning(f"command not found: {args[0]}")
            return 127, ""
