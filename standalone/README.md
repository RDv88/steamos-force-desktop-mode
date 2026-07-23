# Force Desktop Mode: standalone app

A small app for Desktop Mode that sets Desktop Mode as the default boot session, with no
dependency on Decky Loader at all. Uses `steamosctl` directly and needs no root permissions,
the same mechanism SteamOS's own "Return to Gaming Mode" button uses.

## Installation

Open a terminal in Desktop Mode (Konsole) and run:

```bash
curl -fsSL https://raw.githubusercontent.com/RDv88/steamos-force-desktop-mode/master/standalone/install.sh | sh
```

No sudo password needed. This installs:

- `~/.local/share/force-desktop-mode/force_desktop_mode.py`: the app itself
- A "Force Desktop Mode" entry in your application menu
- A user-level systemd service that checks every minute the default hasn't drifted (auto-heal)
- A KDE logout hook so a plain "Log Out" from Desktop Mode returns you to Game Mode instead of
  relaunching Desktop Mode, mirroring SteamOS's own "Return to Gaming Mode" behavior

## Usage

Open "Force Desktop Mode" from your application menu. It shows the current status and lets you:

- Set Desktop Mode or Game Mode as the default
- Reapply the current setting immediately
- Turn the auto-heal background check on/off
- Check for updates

The app also does a quick update check (with a short timeout, skipped silently if you're offline)
every time you open it. That's useful since you'll most likely open this app exactly when
something broke after a SteamOS update.

## Compatibility

Tested on Steam Deck. Should work on Steam Machine too, since both use the same `steamosctl`
mechanism. Feedback from Steam Machine users is welcome via Issues.

## Uninstalling

```bash
curl -fsSL https://raw.githubusercontent.com/RDv88/steamos-force-desktop-mode/master/standalone/uninstall.sh | sh
```

## License

BSD-3-Clause, see [LICENSE](../LICENSE).
