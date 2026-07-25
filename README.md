# Force Desktop Mode

Sets **Desktop Mode** as the default boot session on SteamOS (Steam Deck and Steam Machine)
instead of Game Mode, and keeps it that way across reboots and SteamOS updates, while still
letting you switch to Game Mode whenever you want, with a normal "Log Out" taking you back there.

## Why not just a console command?

`steamosctl set-default-login-mode desktop` does the one-time switch, and that's genuinely all
you need if you don't mind reapplying it after updates. This tool exists for everything around
that single command:

- **Update-resistant**: SteamOS updates can silently reset the default. A background check
  reapplies your choice automatically, so you don't have to remember to check after every update.
- **Correct session handling**: SteamOS has changed its session naming more than once (e.g. the
  old `plasma-persistent` split into X11/Wayland-specific variants). This tool uses `steamosctl`
  directly, the same official mechanism SteamOS's own "Return to Gaming Mode" button uses, so it
  isn't tied to a specific display server and keeps working across those changes.
- **Sensible logout behavior**: a plain "Log Out" from Desktop Mode would otherwise just autologin
  back into Desktop Mode again. A small logout hook sends you back to Game Mode instead, without
  needing to click "Return to Gaming Mode" yourself.

There are two independent ways to install this, pick whichever fits you:

## Version A: Standalone app

Open a terminal in Desktop Mode (Konsole) and run:

```bash
curl -fsSL https://raw.githubusercontent.com/RDv88/steamos-force-desktop-mode/master/standalone/install.sh | sh
```

See [`standalone/README.md`](standalone/README.md) for details and installation instructions.

## Version B: Decky plugin

For people who already have [Decky Loader](https://decky.xyz) installed. Download the latest
zip from [Releases](https://github.com/RDv88/steamos-force-desktop-mode/releases) and install it
via Decky's "Install Plugin from Zip".

See [`decky/README.md`](decky/README.md) for details and installation instructions.

## License

BSD-3-Clause, see [LICENSE](LICENSE).
