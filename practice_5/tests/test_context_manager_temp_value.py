from contextlib import contextmanager
from context_manager_temp_value import temporary_value


def test_key_exists():
    settings = {"mode": "normal"}
    with temporary_value(settings, "mode", "debug"):
        assert settings["mode"] == "debug"
    assert settings["mode"] == "normal"
