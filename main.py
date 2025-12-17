"""Entry point for the Ghostline Browser UI shell."""

import ctypes.util
import importlib.util
import sys


def ensure_ui_requirements() -> None:
    """Validate that graphical dependencies are available before launching."""

    missing = []

    if importlib.util.find_spec("PySide6") is None:
        missing.append("PySide6 (install via `pip install -r requirements.txt`)")

    if ctypes.util.find_library("GL") is None:
        missing.append("libGL (install your platform's OpenGL drivers)")

    if missing:
        formatted = "\n - ".join(missing)
        sys.stderr.write(
            "Ghostline Browser UI is missing required graphical dependencies:\n - "
            f"{formatted}\n"
            "Install the listed dependencies and re-run `python main.py`.\n"
        )
        sys.exit(1)


def main() -> None:
    """Launch the Ghostline Browser UI after verifying dependencies."""

    ensure_ui_requirements()

    from ghostline.ui.app import launch

    launch()


if __name__ == "__main__":
    main()
