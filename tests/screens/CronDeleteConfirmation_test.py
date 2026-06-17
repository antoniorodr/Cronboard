import pytest
from cronboard.services.messages import CronJobDeleted
from cronboard.screens.CronDeleteConfirmation import CronDeleteConfirmation
from tests.conftest import create_event, create_job_and_cron, make_remote_command
from cronboard.app import CronBoard
from pytest_mock import MockerFixture


@pytest.mark.asyncio
async def test_open_delete_cronjob_modal(app: CronBoard):
    async with app.run_test() as pilot:
        await pilot.press("D")
        assert isinstance(app.screen, CronDeleteConfirmation)


@pytest.mark.asyncio
async def test_delete_cronjob_cancel(app: CronBoard):
    async with app.run_test() as pilot:
        await pilot.press("D")
        await pilot.press("tab")
        await pilot.press("enter")
        assert not isinstance(app.screen, CronDeleteConfirmation)


@pytest.mark.asyncio
async def test_delete_cronjob_confirm(app: CronBoard):
    async with app.run_test() as pilot:
        await pilot.press("D")
        await pilot.press("enter")
        assert not isinstance(app.screen, CronDeleteConfirmation)


def test_delete_cronjob_local_write(mocker: MockerFixture):
    job, cron = create_job_and_cron(mocker)
    modal = CronDeleteConfirmation(job=job, cron=cron)
    modal.dismiss = mocker.Mock()
    event = create_event("delete")

    modal.on_button_pressed(event)

    cron.remove.assert_called_once_with(job)
    cron.write.assert_called_once_with()
    modal.dismiss.assert_called_once_with(True)


def test_delete_cronjob_remote_write(mocker: MockerFixture):
    job, cron = create_job_and_cron(mocker)
    _, _, ssh_client = make_remote_command(mocker)
    modal = CronDeleteConfirmation(
        job=job, cron=cron, remote=True, ssh_client=ssh_client
    )
    modal.dismiss = mocker.Mock()
    modal.write_remote_crontab = mocker.Mock(return_value=True)
    event = create_event("delete")

    modal.on_button_pressed(event)

    cron.remove.assert_called_once_with(job)
    cron.write.assert_not_called()
    modal.write_remote_crontab.assert_called_once_with()
    modal.dismiss.assert_called_once_with(True)


def test_delete_cronjob_posts_cron_job_deleted_local(mocker: MockerFixture):
    job, cron = create_job_and_cron(mocker)
    job.comment = "my-job"
    mock_app = mocker.Mock()
    mocker.patch.object(
        CronDeleteConfirmation,
        "app",
        new_callable=mocker.PropertyMock,
        return_value=mock_app,
    )
    mocker.patch.object(
        CronDeleteConfirmation,
        "is_mounted",
        new_callable=mocker.PropertyMock,
        return_value=True,
    )
    modal = CronDeleteConfirmation(job=job, cron=cron)
    modal.dismiss = mocker.Mock()
    event = create_event("delete")

    modal.on_button_pressed(event)

    mock_app.post_message.assert_called_once()
    msg = mock_app.post_message.call_args[0][0]
    assert isinstance(msg, CronJobDeleted)
    assert msg.identificator == "my-job"
    assert msg.ssh_client is None


def test_delete_cronjob_posts_cron_job_deleted_remote(mocker: MockerFixture):
    job, cron = create_job_and_cron(mocker)
    job.comment = "r-job"
    _, _, ssh_client = make_remote_command(mocker)
    mock_app = mocker.Mock()
    mocker.patch.object(
        CronDeleteConfirmation,
        "app",
        new_callable=mocker.PropertyMock,
        return_value=mock_app,
    )
    mocker.patch.object(
        CronDeleteConfirmation,
        "is_mounted",
        new_callable=mocker.PropertyMock,
        return_value=True,
    )
    modal = CronDeleteConfirmation(
        job=job, cron=cron, remote=True, ssh_client=ssh_client
    )
    modal.dismiss = mocker.Mock()
    modal.write_remote_crontab = mocker.Mock(return_value=True)
    event = create_event("delete")

    modal.on_button_pressed(event)

    msg = mock_app.post_message.call_args[0][0]
    assert isinstance(msg, CronJobDeleted)
    assert msg.identificator == "r-job"
    assert msg.ssh_client is ssh_client


def test_write_remote_crontab(mocker: MockerFixture):
    cron, _ = create_job_and_cron(mocker)
    cron.render.return_value = "* * * * * echo hello"
    stdin, stderr, ssh_client = make_remote_command(mocker)

    modal = CronDeleteConfirmation(
        cron=cron, remote=True, ssh_client=ssh_client, crontab_user="root"
    )

    result = modal.write_remote_crontab()

    assert result is True
    ssh_client.exec_command.assert_called_once_with("crontab -u root -")
    stdin.write.assert_called_once_with("* * * * * echo hello")
    stdin.channel.shutdown_write.assert_called_once_with()


def test_write_remote_crontab_error(mocker: MockerFixture):
    cron, _ = create_job_and_cron(mocker)
    cron.render.return_value = "* * * * * echo hello"
    stdin, stderr, ssh_client = make_remote_command(
        mocker, stderr_output=b"Error writing crontab", exit_status=1
    )

    modal = CronDeleteConfirmation(cron=cron, remote=True, ssh_client=ssh_client)

    result = modal.write_remote_crontab()

    assert result is False
    ssh_client.exec_command.assert_called_once_with("crontab -")
