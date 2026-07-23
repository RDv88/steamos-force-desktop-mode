# Force Desktop Mode: Decky plugin

A Decky plugin for SteamOS (Steam Deck and Steam Machine) that sets **Desktop Mode** as your
default boot session instead of Game Mode, using `steamosctl` directly, and keeps it that way
across reboots and SteamOS updates. A plain "Log Out" from Desktop Mode still takes you back to
Game Mode instead of relaunching Desktop Mode, via a KDE logout hook that mirrors SteamOS's own
"Return to Gaming Mode" button.

## Requirements

This is a plugin for [Decky Loader](https://decky.xyz); it does not work standalone. If you
don't have Decky Loader installed on your Steam Deck/Machine yet, install that first.

## Installation

With Decky Loader installed, download the latest zip from
[Releases](https://github.com/RDv88/steamos-force-desktop-mode/releases) and install it via
Decky's Developer Mode (Quick Access Menu → settings → Developer Mode) using
"Install Plugin from Zip".

## Usage

Open the plugin from Decky's Quick Access Menu. It shows the current status and lets you:

- Set Desktop Mode or Game Mode as the default
- Reapply the current setting immediately
- Turn the auto-heal background check on/off
- Refresh the status manually

## Compatibility

Tested on Steam Deck. Should work on Steam Machine too, since both use the same `steamosctl`
mechanism. Feedback from Steam Machine users is welcome via Issues.

## Uninstalling

Uninstall via Decky's plugin manager, which also removes the logout hook.

## Development

From this directory:

```bash
pnpm install
pnpm run build
```

Then either symlink this folder into `~/homebrew/plugins/` on your Deck/Machine for live testing,
or build a fresh installable zip with the [Decky CLI](https://github.com/SteamDeckHomebrew/cli)
from the repo root (output lands in `out/`, relative to wherever you run it from):

```bash
./cli/decky plugin build ./decky
```

## License

BSD-3-Clause, see [LICENSE](LICENSE).
