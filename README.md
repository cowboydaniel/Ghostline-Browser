# Ghostline Browser

A minimal PySide6-based web browser that can open any webpage using Qt WebEngine.

## Requirements

- Python 3.10+
- PySide6 (install with `pip install -r requirements.txt`)

## Running the browser

```bash
pip install -r requirements.txt
python main.py
```

Use the navigation toolbar to go back, forward, reload, return to the home page, or type a URL into the address bar to visit any site. If you enter a domain without a scheme, the browser will automatically prepend `https://`.
