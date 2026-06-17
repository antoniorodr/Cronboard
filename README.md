# `cronboard`

>[!important]
>Cronboard was selected as the [Terminal Trove Tool of the Week](https://terminaltrove.com/cronboard/) in October 28th 2025! 

> [!caution]
> **Status:** Under development


## ℹ️ About

Cronboard is a terminal application for managing and scheduling cron jobs on local and remote servers. You can add, edit, pause, resume, search, and delete jobs from a Textual-based interface.

Full documentation is available at [cronboard.dev](https://cronboard.dev).

## 🎬 Demo

![Cronboard demo](./assets/cronboard.gif)

## ✨ Features

- Check cron jobs, view the logs, and detect potential issues when running
- Autocompletion for paths when creating or editing cron jobs
- Create cron jobs with validation and human-readable feedback
- Pause/resume, edit and delete cron jobs
- View formatted last and next run times
- Accept `special expressions` like `@daily`, `@yearly`, and `@monthly`
- Connect to servers over SSH with either a password or SSH keys
- Manage cron jobs for another user when you have the required `sudo` permissions
- Search for cron jobs using case-insensitive keywords

## 🛠️ Technologies

The project is built with:

- [Textual](https://textual.textualize.io)
- [python-crontab](https://pypi.org/project/python-crontab/)
- [Paramiko](https://github.com/paramiko/paramiko)
- [cron-descriptor](https://github.com/Salamek/cron-descriptor)

## 📋 Requirements

Before starting, make sure `cron` is installed and available on your machine:

```bash
where crontab
```

If you install Cronboard with `pip` or `uv`, you also need Python 3.13 or newer.

## 📦 Installation

For installation instructions, please refer to the [official documentation](https://cronboard.dev/installation).

## 🚀 Getting Started

Once installed, run:

```bash
cronboard
```

Cronboard includes a footer, provided by [Textual](https://textual.textualize.io), that shows the available commands.

> [!note]
> When connecting to a remote server with an SSH key, Cronboard looks for the `known_hosts` file in the default location: `~/.ssh/known_hosts`.

> [!important]
> If you choose to manage cron jobs for another user, make sure you have the necessary permissions. In practice, that means you need `sudo` access.

### ⌨️ Autocompletion

Path autocompletion when creating or editing cron jobs helps you enter file paths faster.

The default starting point for autocompletion is the home directory of the user whose cron jobs you are managing. Accept a suggestion with the `Tab` key.

## ❤️ Do you like my work?

If you find the project useful, you can support the author here:

[![GitHub Sponsor](https://img.shields.io/badge/Sponsor_on_GitHub-30363D?logo=github&style=for-the-badge)](https://github.com/sponsors/antoniorodr)
