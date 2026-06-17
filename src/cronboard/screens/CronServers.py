from textual.app import ComposeResult
from textual.containers import Horizontal, Grid
from textual.widget import Widget
from textual.widgets import Label, Tree
from cronboard.widgets.CronTree import CronTree
from textual.binding import Binding
from cronboard.screens.CronSSHModal import CronSSHModal
from cronboard.widgets.CronTable import CronTable
from cronboard.screens.CronDeleteConfirmation import CronDeleteConfirmation
import paramiko
import tomllib
import tomlkit
from cronboard.services.encryption.CronEncrypt import decrypt_password, encrypt_password
from cronboard.config import CONFIG_FILE


class CronServers(Widget):
    BINDINGS = [
        Binding("a", "add_server", "Add Server"),
        Binding("D", "delete_server", "Delete Server"),
        Binding("c", "connect_server", "Connect"),
        Binding("d", "disconnect_server", "Disconnect Server"),
        Binding("J", "jump", "Switch Panel"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.servers = self.load_servers()
        self.current_ssh_client = None
        self.current_cron_table = None
        self.current_server_name = None

    def compose(self) -> ComposeResult:
        servers_tree = CronTree("Servers", id="servers-tree")
        servers_tree.root.expand()
        self.content_area = Label(
            "Use 'a' on the tree view to add a server", id="disconnected"
        )
        yield Grid(
            Horizontal(
                servers_tree,
                self.content_area,
            ),
            id="servers-grid",
        )

    def on_mount(self) -> None:
        servers_tree = self.query_one("#servers-tree", Tree)
        for server_id, server_info in self.servers.items():
            servers_tree.root.add_leaf(
                f"{server_info['name']}: {server_info.get('crontab_user', '')}",
                server_id,
            )
        servers_tree.refresh()

    def action_connect_server(self) -> None:
        servers_tree = self.query_one("#servers-tree", Tree)
        if servers_tree.cursor_node and servers_tree.cursor_node != servers_tree.root:
            server_id = servers_tree.cursor_node.data
            server_info = self.servers.get(server_id)
            if server_info:
                self.connect_to_server(server_info)

    def connect_to_server(self, server_info) -> None:
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.load_system_host_keys()
            ssh_client.set_missing_host_key_policy(paramiko.WarningPolicy)

            host = server_info["host"]
            port = server_info["port"]
            username = server_info["username"]
            password = server_info["password"]
            crontab_user = server_info.get("crontab_user")

            if server_info["ssh_key"]:
                ssh_client.connect(hostname=host, port=port, username=username)
            else:
                ssh_client.connect(
                    hostname=host, port=port, username=username, password=password
                )

            if self.current_ssh_client:
                try:
                    self.current_ssh_client.close()
                except:
                    pass

            self.current_ssh_client = ssh_client
            self.current_server_name = server_info["name"]
            self.show_cron_table_for_server(ssh_client, server_info, crontab_user)

            server_info["connected"] = True
            self.save_servers()

            self.notify(f"Connected to {server_info['name']}")

        except paramiko.AuthenticationException:
            self.notify("Authentication failed. Please check your credentials.")
        except Exception as e:
            self.notify(f"Connection error: {e}")

    def show_cron_table_for_server(self, ssh_client, server_info, crontab_user) -> None:
        if self.current_cron_table:
            self.current_cron_table.ssh_client = ssh_client
            self.current_cron_table.remote = True
            self.current_cron_table.crontab_user = crontab_user
            self.current_cron_table.action_refresh()
            self.notify(f"Switched to {server_info['name']}")
            return

        self.current_cron_table = CronTable(
            remote=True,
            ssh_client=ssh_client,
            id="remote-cron-table",
            crontab_user=crontab_user,
        )

        container = self.query_one("#servers-grid", Grid)
        horizontal = container.query_one(Horizontal)

        if self.content_area and self.content_area != self.current_cron_table:
            self.content_area.remove()

        horizontal.mount(self.current_cron_table)
        self.content_area = self.current_cron_table

    def show_disconnected_message(self) -> None:
        if self.current_cron_table:
            self.current_cron_table.remove()
            self.current_cron_table = None

        disconnected_label = Label(
            "Use 'a' on the tree view to add a server", id="disconnected"
        )

        container = self.query_one("#servers-grid", Grid)
        horizontal = container.query_one(Horizontal)

        if self.content_area:
            self.content_area.remove()

        horizontal.mount(disconnected_label)
        self.content_area = disconnected_label

    def action_disconnect_server(self) -> None:
        if self.current_ssh_client:
            try:
                self.current_ssh_client.close()
                self.show_disconnected_message()
            except:
                pass
            self.current_ssh_client = None

        for server_info in self.servers.values():
            server_info["connected"] = False

        connected_server_name = self.current_server_name
        self.current_server_name = None

        if connected_server_name:
            self.notify(f"Disconnected from server {connected_server_name}")
        else:
            self.notify("You are not connected to any server")

        self.save_servers()

    def load_servers(self) -> dict:
        if CONFIG_FILE.exists():
            try:
                with CONFIG_FILE.open("rb") as f:
                    loaded_servers = tomllib.load(f)

                for server_id, server_info in loaded_servers.items():
                    if "encrypted_password" in server_info:
                        encrypted_password = server_info.pop("encrypted_password")
                        if encrypted_password:
                            try:
                                server_info["password"] = decrypt_password(
                                    encrypted_password
                                )
                            except Exception as e:
                                print(
                                    f"❌ Failed to decrypt password for {server_id}: {e}"
                                )
                                server_info["password"] = None
                        else:
                            server_info["password"] = None
                    elif "password" not in server_info:
                        server_info["password"] = None

                    if "crontab_user" not in server_info:
                        server_info["crontab_user"] = None

                return loaded_servers
            except Exception as e:
                print(f"❌ Warning: Failed to load servers: {e}")
        else:
            print("📝 No servers file found, starting with empty list")
        return {}

    def save_servers(self) -> None:
        try:
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            toml_safe_servers = {}
            for server_id, server_info in self.servers.items():
                encrypted_password = ""
                if server_info.get("password"):
                    encrypted_password = encrypt_password(server_info["password"])

                toml_safe_servers[server_id] = {
                    "name": server_info["name"],
                    "host": server_info["host"],
                    "port": server_info["port"],
                    "username": server_info["username"],
                    "encrypted_password": encrypted_password,
                    "ssh_key": server_info["ssh_key"],
                    "connected": server_info["connected"],
                    "crontab_user": server_info.get("crontab_user")
                    if server_info.get("crontab_user")
                    else server_info["username"],
                }

            with CONFIG_FILE.open("w", encoding="utf-8") as f:
                tomlkit.dump(toml_safe_servers, f)
        except Exception as e:
            self.notify(f"❌ Error: Failed to save servers: {e}")

    def action_add_server(self) -> None:
        def on_server_added(result):
            if result:
                name = result.get("username") + "@" + result.get("hostname")
                host = result.get("hostname")
                port = result.get("port")
                username = result.get("username")
                password = result.get("password") if result.get("password") else None
                crontab_user = result.get("crontab_user")
                self.add_server_to_tree(
                    name, host, port, username, password, crontab_user
                )

        cron_ssh_modal = CronSSHModal()
        self.app.push_screen(cron_ssh_modal, on_server_added)

    def add_server_to_tree(
        self,
        name: str,
        host: str,
        port: str,
        username: str,
        password: str | None,
        crontab_user: str | None = None,
    ) -> None:
        servers_tree = self.query_one("#servers-tree", Tree)
        server_id = f"{username}@{host}:{crontab_user}"
        if server_id not in self.servers:
            self.servers[server_id] = {
                "name": name,
                "host": host,
                "port": port,
                "username": username,
                "password": password,
                "ssh_key": True if not password else False,
                "connected": False,
                "crontab_user": crontab_user,
            }
            servers_tree.root.add_leaf(
                f"{name}: {crontab_user if crontab_user else username}", server_id
            )
            servers_tree.refresh()
            self.save_servers()

    def action_delete_server(self) -> None:
        servers_tree = self.query_one("#servers-tree", Tree)
        if not (
            servers_tree.cursor_node and servers_tree.cursor_node != servers_tree.root
        ):
            self.notify("No server selected to delete.")
            return

        server_id = servers_tree.cursor_node.data
        server_info = self.servers.get(server_id)

        if not server_info:
            self.notify("Selected server not found.")
            return

        def on_delete_confirmed(confirmed: bool) -> None:
            if confirmed:
                if self.current_ssh_client:
                    self.action_disconnect_server()

                del self.servers[server_id]
                servers_tree.cursor_node.remove()
                self.save_servers()
                self.notify(f"Deleted server {server_info['name']}")
            else:
                self.notify("Server deletion cancelled.")

        confirmation_modal = CronDeleteConfirmation(
            message=f"Are you sure you want to delete the server '{server_info['name']}' ?",
        )
        self.app.push_screen(confirmation_modal, on_delete_confirmed)

    def focus_tree(self):
        try:
            self._focus_tree()
        except:
            self.call_after_refresh(self._focus_tree)

    def _focus_tree(self):
        tree = self.query_one("#servers-tree", Tree)
        if tree:
            tree.focus()

    def action_jump(self) -> None:
        servers_tree = self.query_one("#servers-tree", Tree)
        if servers_tree.has_focus and self.current_cron_table:
            self.current_cron_table.focus()
        else:
            servers_tree.focus()
