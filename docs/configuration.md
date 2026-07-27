\# Configuration



Cronboard stores its configuration in the user's home directory under `\~/.config/cronboard/`.



\---



\## Config Files



| File                               | Purpose                       |

| ---------------------------------- | ----------------------------- |

| `\~/.config/cronboard/config.toml`  | General settings (e.g. theme) |

| `\~/.config/cronboard/servers.toml` | Saved SSH servers             |



These files are created automatically the first time you run Cronboard. You do not need to edit them manually.



\---



\## Theme



Cronboard is built on \[Textual](https://textual.textualize.io), which ships with several built-in themes.



The active theme is saved automatically whenever you change it inside the application. The default theme is \*\*`catppuccin-mocha`\*\*.



To change the theme, open the command palette with \*\*`Ctrl+P`\*\* (or \*\*`Ctrl+E`\*\* on some setups), type `theme`, and choose a theme. Your choice is written to `config.toml` so it persists across restarts.



\### `config.toml` example



```toml

theme = "catppuccin-mocha"

