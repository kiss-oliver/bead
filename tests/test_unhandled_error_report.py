import pytest

from bead_cli.main import main


class UnhandledError(Exception):
    pass


def _deep_exception(n=4):
    if n == 0:
        raise UnhandledError
    _deep_exception(n - 1)


def failing_run(config_dir, argv):
    _deep_exception()


def test_unhandled_error(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)

    argv = ['1', 'unhandled', 'ecxeptipons']
    argv_text = f'{argv}'
    monkeypatch.setattr('sys.argv', argv)

    with pytest.raises(SystemExit):
        main(run=failing_run)

    stderr = capsys.readouterr().err
    error_report_path, = list(tmp_path.glob('error_*.txt'))

    # stderr is what the user see
    assert 'UnhandledError' in stderr
    assert f'{error_report_path}' in stderr

    # error report is the file written with the error details
    error_report_text = error_report_path.read_text()
    assert 'UnhandledError' in error_report_text
    assert argv_text in error_report_text
    assert error_report_text.count('_deep_exception') > 3
