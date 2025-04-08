"""Dark theme style definitions for the application."""

MAIN_WINDOW_STYLE = """
    QMainWindow {
        background-color: #1b1e23;
    }
    * {
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }
"""

TOP_BAR_STYLE = """
    QFrame {
        background-color: #0d1117;
        border: none;
    }
"""

VERSION_LABEL_STYLE = """
    color: #ffffff;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-weight: 400;
"""

WINDOW_CONTROLS_BUTTON_STYLE = """
    QPushButton {
        color: #ffffff;
        border: none;
        font-family: 'Segoe UI', 'Arial', sans-serif;
        font-size: 16px;
        font-weight: 400;
        background-color: #0d1117;
    }
    QPushButton:hover {
        background-color: #1f2937;
    }
"""

CLOSE_BUTTON_STYLE = """
    QPushButton {
        color: #ffffff;
        border: none;
        font-family: 'Segoe UI', 'Arial', sans-serif;
        font-size: 16px;
        font-weight: 400;
        background-color: #0d1117;
    }
    QPushButton:hover {
        background-color: #ff5555;
    }
"""

SIDEBAR_STYLE = """
    QFrame {
        background-color: #2c313c;
        border: none;
    }
    QPushButton {
        color: #ffffff;
        text-align: left;
        padding: 10px;
        padding-left: 15px;
        border: none;
        font-family: 'Segoe UI', 'Arial', sans-serif;
        font-size: 13px;
        font-weight: 400;
        letter-spacing: 0.3px;
    }
    QPushButton:hover {
        background-color: #3c4454;
    }
"""

CONTENT_AREA_STYLE = """
    QFrame {
        background-color: #1b1e23;
        border: none;
    }
""" 