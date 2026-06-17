# Installation

Before installing Cronboard, make sure `cron` is available on your machine:

```bash
where crontab
```

If this command returns an error saying `cron` is not installed, install it through your system's package manager first. Cronboard only manages existing crontabs; it does not replace the system cron daemon.

---

## Homebrew (macOS / Linux)

Recommended if you use Homebrew. You get automatic updates with `brew upgrade`.

```bash
brew install cronboard
```

---

## uv

Good choice if you already use [uv](https://github.com/astral-sh/uv) for Python tooling. Installs the latest version from [PyPI](https://pypi.org/project/cronboard/). You can update the install with `uv tool update cronboard` when new versions are released.

```bash
uv tool install cronboard
```

---

## AUR (Arch Linux)

For Arch users. Install from the AUR with your preferred helper (e.g. `yay` or `paru`).

```bash
yay -S cronboard
```

---

## Nix

For Nix/NixOS users. Adds Cronboard to your profile from the project’s flake.

```bash
nix profile add github:antoniorodr/cronboard
```

---

## Manual (from source)

Use this if you want to run from a clone (e.g. for development or a specific branch). Requires Python 3.13+ and the project’s dependencies.

```bash
git clone https://github.com/antoniorodr/cronboard
cd cronboard
pip install .
```
