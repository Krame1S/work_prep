from context_manager_temp_value import temporary_value
import pytest


def test_key_exists():
    original = []
    settings = {"mode": original}

    with temporary_value(settings, "mode", "debug"):
        assert settings["mode"] == "debug"

    assert settings["mode"] is original


def test_key_doesnt_exist():
    settings = {}

    with temporary_value(settings, "mode", "debug"):
        assert settings["mode"] == "debug"

    assert "mode" not in settings


def test_initial_none():
    settings = {"mode": None}

    with temporary_value(settings, "mode", "debug"):
        pass

    assert "mode" in settings
    assert settings["mode"] is None


def test_exception_in_block():
    settings = {"mode": "normal"}

    with pytest.raises(ValueError):
        with temporary_value(settings, "mode", "debug"):
            raise ValueError

    assert settings["mode"] == "normal"


def test_exception_in_block_key_doesnt_exist():
    settings = {}

    with pytest.raises(ValueError):
        with temporary_value(settings, "mode", "debug"):
            raise ValueError

    assert "mode" not in settings


def test_other_key_changes_kept():
    settings = {"mode": "normal", "level": 1}

    with temporary_value(settings, "mode", "debug"):
        settings["level"] = 2
        settings["extra"] = True

    assert settings == {"mode": "normal", "level": 2, "extra": True}


def test_two_nested_contexts():
    settings = {"mode": "normal"}

    with temporary_value(settings, "mode", "debug"):
        with temporary_value(settings, "mode", "trace"):
            assert settings["mode"] == "trace"
        assert settings["mode"] == "debug"

    assert settings["mode"] == "normal"
