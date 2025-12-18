from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt
from src.ui.theme import Theme

class CardWidget(QFrame):
    """
    A styled container widget acting as a 'Card'.
    """
    def __init__(self, title: str = None, parent=None):
        super().__init__(parent)
        self.setup_ui(title)

    def setup_ui(self, title):
        self.setObjectName("CardWidget")
        self.setStyleSheet(f"""
            #CardWidget {{
                background-color: {Theme.SURFACE};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(8)
        
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-weight: bold; font-size: 11px; text-transform: uppercase;")
            self.layout.addWidget(title_label)

    def add_widget(self, widget: QWidget):
        self.layout.addWidget(widget)
        
    def add_layout(self, layout):
        self.layout.addLayout(layout)

class DashboardCard(CardWidget):
    """
    A specific card for displaying a statistic.
    """
    def __init__(self, title: str, start_value: str = "0", color: str = None, parent=None):
        super().__init__(title, parent)
        
        self.value_label = QLabel(start_value)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Style
        text_color = color if color else Theme.TEXT_PRIMARY
        self.value_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {text_color};
        """)
        
        self.add_widget(self.value_label)

    def set_value(self, value: str):
        self.value_label.setText(value)
