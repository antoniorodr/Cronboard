# Configuration

Cronboard stores its configuration in the user's home directory under `~/.config/cronboard/`.

---

## Config Files

| File                               | Purpose                       |
| ---------------------------------- | ----------------------------- |
| `~/.config/cronboard/config.toml`  | General settings (e.g. theme) |
| `~/.config/cronboard/servers.toml` | Saved SSH servers             |

These files are created automatically the first time you run Cronboard. You do not need to edit them manually.

---

## Theme

Cronboard is built on [Textual](https://textual.textualize.io), which ships with several built-in themes.

The active theme is saved automatically whenever you change it inside the application. The default theme is **`catppuccin-mocha`**.

To change the theme, open the command palette with **`Ctrl+P`** (or **`Ctrl+E`** on some setups), type `theme`, and choose a theme. Your choice is written to `config.toml` so it persists across restarts.

### `config.toml` example

```toml
theme = "catppuccin-mocha"
```

---

## Saved Servers

The `servers.toml` file holds the list of SSH servers you have added. Each server entry looks like this:

```toml
[username@host:crontab_user]
name = "username@hostname"
host = "hostname"
port = 22
username = "username"
encrypted_password = "<bcrypt-encrypted>"
ssh_key = false
connected = false
crontab_user = "username"
```

>Passwords are **never stored in plain text**, they are encrypted with `bcrypt` before being written to disk.

## Telegram Notifications

Telegram notifications are disabled by default. To enable them, add your Telegram token and chat ID from the settings panel of the Cronboard application, and set `notifications` to `enabled`.

### How can I get Telegram bot token and chat ID?

To create a Telegram bot and obtain the bot token and chat ID, you'll need to follow these steps:

#### Create a Telegram Bot:

1. Open the Telegram app and search for the "BotFather" (username: @BotFather).
2. Start a chat with BotFather and use the command "/newbot" to create a new bot.
3. Follow the instructions provided by BotFather to choose a name and username for your bot. d. Once the bot is created, BotFather will provide you with a unique API token. This token is your bot token, and you will need it to authenticate and interact with the Telegram Bot API.

#### Obtain your Chat ID:
1. Add your newly created bot to the desired Telegram chat or group where you want to receive messages.
2. Open a web browser and enter the following URL, replacing <YourBotToken> with the token you received from BotFather:
https://api.telegram.org/bot<YourBotToken>/getUpdates
3. You should see a JSON response that contains information about the most recent messages received by your bot.
4. Look for the "chat" object in the response, which contains details about the chat your bot is part of.
5. The "id" field within the "chat" object corresponds to the chat ID of the group or channel. Make note of this chat ID; you will need it to send messages to the chat.

>The Telegram bot token and chat ID are **never stored in plain text**, they are encrypted with `OpenSSL` before being written to disk.
