from PyQt6.QtGui import QColor

class Theme:
    """
    Defines the color palette and styles for the application.
    """
    # Colors
    BACKGROUND = "#1E1E1E"
    SURFACE = "#252526"
    SURFACE_LIGHT = "#2D2D2D"
    BORDER = "#3E3E42"
    
    TEXT_PRIMARY = "#CCCCCC"
    TEXT_SECONDARY = "#969696"
    
    ACCENT = "#007ACC"
    ACCENT_HOVER = "#0098FF"
    
    SUCCESS = "#4CAF50"
    WARNING = "#FFC107"
    ERROR = "#F44336"
    
    # Log Levels
    LOG_VERBOSE = "#9E9E9E"
    LOG_DEBUG = "#4CAF50"
    LOG_INFO = "#2196F3"
    LOG_WARN = "#FFC107"
    LOG_ERROR = "#F44336"
    LOG_FATAL = "#B71C1C"

    @staticmethod
    def get_app_stylesheet():
        """Returns the global QSS stylesheet"""
        return f"""
            QMainWindow, QWidget {{
                background-color: {Theme.BACKGROUND};
                color: {Theme.TEXT_PRIMARY};
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }}
            
            /* Inputs */
            QLineEdit, QPlainTextEdit, QTextEdit {{
                background-color: {Theme.SURFACE_LIGHT};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 4px;
                color: {Theme.TEXT_PRIMARY};
                selection-background-color: {Theme.ACCENT};
            }}
            QLineEdit:focus, QPlainTextEdit:focus {{
                border: 1px solid {Theme.ACCENT};
            }}
            
            /* Buttons */
            QPushButton {{
                background-color: {Theme.SURFACE_LIGHT};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 6px 12px;
                color: {Theme.TEXT_PRIMARY};
            }}
            QPushButton:hover {{
                background-color: {Theme.BORDER};
            }}
            QPushButton:pressed {{
                background-color: {Theme.SURFACE};
            }}
            QPushButton:disabled {{
                color: {Theme.TEXT_SECONDARY};
                background-color: {Theme.SURFACE};
                border: 1px solid {Theme.SURFACE};
            }}
            
            /* Tables/Lists */
            QTableView, QListWidget {{
                background-color: {Theme.BACKGROUND};
                border: 1px solid {Theme.BORDER};
                gridline-color: {Theme.BORDER};
                selection-background-color: {Theme.SURFACE_LIGHT};
                selection-color: {Theme.TEXT_PRIMARY};
                outline: none;
            }}
            QHeaderView::section {{
                background-color: {Theme.SURFACE};
                color: {Theme.TEXT_SECONDARY};
                padding: 4px;
                border: none;
                border-right: 1px solid {Theme.BORDER};
                border-bottom: 1px solid {Theme.BORDER};
            }}
            QTableView::item {{
                padding: 2px;
            }}
            
            /* Tabs */
            QTabWidget::pane {{
                border: 1px solid {Theme.BORDER};
                top: -1px;
            }}
            QTabBar::tab {{
                background-color: {Theme.SURFACE};
                color: {Theme.TEXT_SECONDARY};
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid {Theme.BORDER};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {Theme.BACKGROUND};
                color: {Theme.TEXT_PRIMARY};
                border-bottom: 1px solid {Theme.BACKGROUND}; 
            }}
            
            /* Scrollbars */
            QScrollBar:vertical {{
                border: none;
                background: {Theme.BACKGROUND};
                width: 10px;
                margin: 0px 0px 0px 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {Theme.BORDER};
                min-height: 20px;
                border-radius: 5px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            /* GroupBox */
            QGroupBox {{
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px; 
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                color: {Theme.TEXT_SECONDARY};
            }}
        """

    @staticmethod
    def get_log_level_color(level_str: str) -> str:
        """Returns the hex color for a given log level letter"""
        mapping = {
            'V': Theme.LOG_VERBOSE,
            'D': Theme.LOG_DEBUG,
            'I': Theme.LOG_INFO,
            'W': Theme.LOG_WARN,
            'E': Theme.LOG_ERROR,
            'F': Theme.LOG_FATAL
        }
        return mapping.get(level_str, Theme.TEXT_PRIMARY)
