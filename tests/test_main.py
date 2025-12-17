import importlib.util

import pytest

import main


def test_ensure_ui_requirements_missing(monkeypatch, capsys):
    monkeypatch.setattr(main.importlib.util, "find_spec", lambda name: None)
    monkeypatch.setattr(main.ctypes.util, "find_library", lambda name: None)

    with pytest.raises(SystemExit) as excinfo:
        main.ensure_ui_requirements()

    assert excinfo.value.code == 1
    stderr = capsys.readouterr().err
    assert "PySide6" in stderr
    assert "libGL" in stderr


def test_ensure_ui_requirements_present(monkeypatch):
    monkeypatch.setattr(main.importlib.util, "find_spec", lambda name: object())
    monkeypatch.setattr(main.ctypes.util, "find_library", lambda name: "/usr/lib/libGL.so")

    main.ensure_ui_requirements()
