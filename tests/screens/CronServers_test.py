from cronboard.screens.CronServers import CronServers


def test_disconnect_notifies_only_current_server(mocker):
    mocker.patch.object(CronServers, "load_servers", return_value={})
    servers = CronServers()
    servers.servers = {
        "server-a": {"name": "server-A", "connected": True},
        "server-b": {"name": "server-B", "connected": False},
        "server-c": {"name": "server-C", "connected": False},
    }
    servers.current_server_name = "server-A"
    ssh_client = mocker.Mock()
    servers.current_ssh_client = ssh_client
    servers.show_disconnected_message = mocker.Mock()
    servers.save_servers = mocker.Mock()
    servers.notify = mocker.Mock()

    servers.action_disconnect_server()

    ssh_client.close.assert_called_once_with()
    servers.notify.assert_called_once_with("Disconnected from server server-A")
    assert all(not server_info["connected"] for server_info in servers.servers.values())
    assert servers.current_server_name is None
