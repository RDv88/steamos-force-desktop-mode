# Force Desktop Mode

Sets **Desktop Mode** as the default boot session on SteamOS (Steam Deck and Steam Machine)
instead of Game Mode, and keeps it that way across reboots and SteamOS updates, while still
letting you switch to Game Mode whenever you want, with a normal "Log Out" taking you back there.

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
