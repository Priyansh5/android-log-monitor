import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QCheckBox, QLineEdit, QComboBox, 
    QMessageBox, QFileDialog, QTabWidget, QSplitter, QGroupBox, QInputDialog, QProgressBar, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QShortcut, QKeySequence

# Internal Imports
from src.config import ConfigManager
from src.adb_utils import ADBUtils
from src.log_capture import LogCapture
from src.file_monitor import FileMonitor
from src.log_parser import LogParser, LogEntry, LogLevel
from src.analysis import LogAnalyzer
from src.filters import LogFilter
from src.export import LogExporter
from src.bookmarks import BookmarkManager
from src.search import LogSearch
from src.filter_presets import FilterPresetManager
from src.timeline_widget import TimelineWidget

# New UI Components
from src.ui.theme import Theme
from src.ui.components import CardWidget, DashboardCard
from src.models.log_model import LogTableModel
from src.views.log_view import LogTableView
from src.models.proxy_model import LogProxyModel


class AndroidLogMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        # Core Systems
        self.config = ConfigManager()
        self.adb_utils = ADBUtils()
        self.log_capture = LogCapture(self.adb_utils)
        self.file_monitor = FileMonitor(self.config)
        self.log_parser = LogParser()
        self.analyzer = LogAnalyzer()
        self.log_filter = LogFilter()
        self.exporter = LogExporter(self.config)
        self.bookmarks = BookmarkManager()
        self.preset_manager = FilterPresetManager()
        
        # State
        self.current_device = None
        self.all_log_entries = []
        self.is_paused = False
        self.paused_logs_buffer = []

        # UI Models
        self.log_model = LogTableModel()
        self.proxy_model = LogProxyModel()
        self.proxy_model.setSourceModel(self.log_model)
        
        self.setup_ui()
        self.setup_connections()
        self.update_device_list()
        
        # Health Check
        self.health_timer = QTimer()
        self.health_timer.timeout.connect(self.check_connection_health)
        self.health_timer.setInterval(5000)

    def setup_ui(self):
        self.setWindowTitle("Android Log Monitor Pro")
        self.resize(1300, 850)
        self.setStyleSheet(Theme.get_app_stylesheet())

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 1. Left Sidebar
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar, 1)

        # 2. Main Content
        content = self.create_content_area()
        main_layout.addWidget(content, 4)

        # Menubar & Statusbar
        self.create_menu_bar()
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

    def create_sidebar(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Device Card
        device_card = CardWidget("Device")
        self.device_combo = QComboBox()
        self.device_combo.currentIndexChanged.connect(self.on_device_selected)
        
        refresh_btn = QPushButton("Refresh List")
        refresh_btn.clicked.connect(self.update_device_list)
        
        device_card.add_widget(self.device_combo)
        device_card.add_widget(refresh_btn)
        
        self.status_indicator = QLabel("Disconnected")
        self.status_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_indicator.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-weight: bold;")
        device_card.add_widget(self.status_indicator)
        
        layout.addWidget(device_card)
        
        # Controls Card
        controls_card = CardWidget("Capture Controls")
        
        self.btn_start = QPushButton("Start Capture")
        self.btn_start.clicked.connect(self.start_monitoring)
        self.btn_start.setStyleSheet(f"background-color: {Theme.ACCENT}; color: white;")
        
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.clicked.connect(self.stop_monitoring)
        self.btn_stop.setEnabled(False)
        
        self.btn_clear = QPushButton("Clear View")
        self.btn_clear.clicked.connect(self.clear_display)
        
        controls_card.add_widget(self.btn_start)
        controls_card.add_widget(self.btn_stop)
        controls_card.add_widget(self.btn_clear)
        
        layout.addWidget(controls_card)
        
        # Session Stats Card
        stats_card = CardWidget("Session Info")
        self.lbl_log_count = QLabel("Logs: 0")
        self.lbl_error_count = QLabel("Errors: 0")
        self.lbl_error_count.setStyleSheet(f"color: {Theme.ERROR}")
        
        stats_card.add_widget(self.lbl_log_count)
        stats_card.add_widget(self.lbl_error_count)
        layout.addWidget(stats_card)
        
        layout.addStretch()
        return container

    def create_content_area(self):
        tabs = QTabWidget()
        
        # Tab 1: Live Logs
        self.log_view = LogTableView()
        self.log_view.setModel(self.proxy_model)
        
        # Container for Search + View
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        log_layout.setContentsMargins(0, 10, 0, 0)
        
        # Search Bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search logs (Ctrl+F)...")
        self.search_input.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_input)
        log_layout.addLayout(search_layout)
        
        log_layout.addWidget(self.log_view)
        tabs.addTab(log_tab, "Live Logs")
        
        # Tab 2: Dashboard (Stats)
        self.dashboard_tab = self.create_dashboard_tab()
        tabs.addTab(self.dashboard_tab, "Statistics")
        
        # Tab 3: Settings/Filters
        self.settings_tab = self.create_settings_tab()
        tabs.addTab(self.settings_tab, "Filters & Settings")
        
        return tabs

    def create_dashboard_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Summary Row (Cards)
        summary_layout = QHBoxLayout()
        self.card_total = DashboardCard("Total Logs")
        self.card_errors = DashboardCard("Errors", color=Theme.ERROR)
        self.card_rate = DashboardCard("Logs / Sec", color=Theme.ACCENT)
        self.card_duration = DashboardCard("Duration")
        
        summary_layout.addWidget(self.card_total)
        summary_layout.addWidget(self.card_errors)
        summary_layout.addWidget(self.card_rate)
        summary_layout.addWidget(self.card_duration)
        
        layout.addLayout(summary_layout)
        
        # Detailed Stats
        details_layout = QHBoxLayout()
        
        # Top Tags
        tags_card = CardWidget("Top Tags")
        self.list_top_tags = QTextEdit()
        self.list_top_tags.setReadOnly(True)
        tags_card.add_widget(self.list_top_tags)
        
        # Top Errors
        errors_card = CardWidget("Top Errors")
        self.list_top_errors = QTextEdit()
        self.list_top_errors.setReadOnly(True)
        errors_card.add_widget(self.list_top_errors)
        
        details_layout.addWidget(tags_card)
        details_layout.addWidget(errors_card)
        
        layout.addLayout(details_layout)
        
        layout.addStretch()
        return tab

    def create_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # 1. Saved Profiles
        profile_card = CardWidget("Saved Profiles")
        profile_layout = QHBoxLayout()
        
        self.profile_combo = QComboBox()
        self.refresh_profiles()
        
        btn_load = QPushButton("Load")
        btn_load.clicked.connect(self.load_profile)
        
        btn_save = QPushButton("Save Current")
        btn_save.clicked.connect(self.save_profile)
        
        profile_layout.addWidget(QLabel("Profile:"))
        profile_layout.addWidget(self.profile_combo, 1)
        profile_layout.addWidget(btn_load)
        profile_layout.addWidget(btn_save)
        
        profile_card.add_layout(profile_layout)
        layout.addWidget(profile_card)

        # 2. Log Levels
        level_card = CardWidget("Log Levels")
        level_layout = QHBoxLayout()
        self.level_checks = {}
        for level in LogLevel:
            cb = QCheckBox(level.name)
            cb.setChecked(True)
            cb.stateChanged.connect(self.refresh_filters)
            self.level_checks[level] = cb
            level_layout.addWidget(cb)
        
        # Quick Level Buttons
        btn_all = QPushButton("All")
        btn_all.clicked.connect(lambda: self.set_levels(True))
        btn_none = QPushButton("None")
        btn_none.clicked.connect(lambda: self.set_levels(False))
        
        level_layout.addStretch()
        level_layout.addWidget(btn_all)
        level_layout.addWidget(btn_none)
        
        level_card.add_layout(level_layout)
        layout.addWidget(level_card)
        
        # 3. Text Filters
        tag_card = CardWidget("Text Filters")
        
        # Tag Filter
        tag_layout = QHBoxLayout()
        self.txt_tag_filter = QLineEdit()
        self.txt_tag_filter.setPlaceholderText("Tag filter (e.g. ActivityManager)")
        self.txt_tag_filter.textChanged.connect(self.refresh_filters)
        tag_layout.addWidget(QLabel("Tag:"))
        tag_layout.addWidget(self.txt_tag_filter)
        
        # Keyword Filter
        kw_layout = QHBoxLayout()
        self.txt_kw_filter = QLineEdit()
        self.txt_kw_filter.setPlaceholderText("Message keyword (e.g. NullPointerException)")
        self.txt_kw_filter.textChanged.connect(self.refresh_filters)
        kw_layout.addWidget(QLabel("Keyword:"))
        kw_layout.addWidget(self.txt_kw_filter)
        
        tag_card.add_layout(tag_layout)
        tag_card.add_layout(kw_layout)
        layout.addWidget(tag_card)
        
        # 4. Active Filters (PID and Excluded Tags)
        active_filters_card = CardWidget("Active Filters")
        
        # PID Filter Display
        pid_layout = QHBoxLayout()
        self.lbl_pid_filter = QLabel("PID Filter: None")
        self.btn_clear_pid = QPushButton("Clear PID")
        self.btn_clear_pid.clicked.connect(self.clear_pid_filter)
        self.btn_clear_pid.setEnabled(False)
        pid_layout.addWidget(self.lbl_pid_filter)
        pid_layout.addWidget(self.btn_clear_pid)
        
        # Excluded Tags Display
        excluded_layout = QHBoxLayout()
        self.lbl_excluded_tags = QLabel("Excluded Tags: None")
        self.btn_clear_excluded = QPushButton("Clear Excluded")
        self.btn_clear_excluded.clicked.connect(self.clear_excluded_tags)
        self.btn_clear_excluded.setEnabled(False)
        excluded_layout.addWidget(self.lbl_excluded_tags)
        excluded_layout.addWidget(self.btn_clear_excluded)
        
        active_filters_card.add_layout(pid_layout)
        active_filters_card.add_layout(excluded_layout)
        layout.addWidget(active_filters_card)

        # 5. Timeline
        timeline_card = CardWidget("Timeline Visualizer")
        self.timeline = TimelineWidget()
        timeline_card.add_widget(self.timeline)
        layout.addWidget(timeline_card)

        layout.addStretch()
        return tab

    def create_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        
        view_menu = menubar.addMenu("View")
        theme_action = view_menu.addAction("Toggle Theme")
        
        help_menu = menubar.addMenu("Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about)

    def setup_connections(self):
        self.file_monitor._on_logs_ready = self.on_new_logs
        
        # Log view signals
        self.log_view.filter_by_tag_requested.connect(self.on_filter_by_tag)
        self.log_view.exclude_tag_requested.connect(self.on_exclude_tag)
        self.log_view.filter_by_pid_requested.connect(self.on_filter_by_pid)
        
        # Shortcuts
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(lambda: self.search_input.setFocus())
        QShortcut(QKeySequence("Ctrl+L"), self).activated.connect(self.clear_display)
        # Ctrl+P for pause
        QShortcut(QKeySequence("Ctrl+P"), self).activated.connect(self.toggle_pause)
        
        # Timeline
        self.timeline.time_range_changed.connect(self.on_timeline_range_changed)

    # --- Core Logic ---
    
    def on_timeline_range_changed(self, start, end):
        self.proxy_model.set_time_filter(start, end)
        if self.log_view.auto_scroll and not start:
             self.log_view.scrollToBottom()

    def start_monitoring(self):
        if not self.current_device:
            QMessageBox.warning(self, "Error", "No device selected")
            return
            
        if self.log_capture.start_capture(self.current_device):
            log_path = self.log_capture.get_log_file_path()
            self.file_monitor.start_monitoring(log_path)
            
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
            self.status_indicator.setText("Monitoring")
            self.status_indicator.setStyleSheet(f"color: {Theme.SUCCESS}; font-weight: bold;")
            self.health_timer.start()

    def stop_monitoring(self):
        self.file_monitor.stop_monitoring()
        self.log_capture.stop_capture()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.status_indicator.setText("Stopped")
        self.status_indicator.setStyleSheet(f"color: {Theme.WARNING}; font-weight: bold;")
        self.health_timer.stop()
        
    def toggle_pause(self):
        self.is_paused = not self.is_paused
        status = "Paused" if self.is_paused else "Monitoring"
        color = Theme.WARNING if self.is_paused else Theme.SUCCESS
        self.status_indicator.setText(status)
        self.status_indicator.setStyleSheet(f"color: {color}; font-weight: bold;")
        
        if not self.is_paused and self.paused_logs_buffer:
             self.on_new_logs(self.paused_logs_buffer)
             self.paused_logs_buffer.clear()

    # --- Profiles Logic ---
    def refresh_profiles(self):
        self.profile_combo.clear()
        self.profile_combo.addItem("-- Select Profile --")
        for p in self.preset_manager.list_presets():
            self.profile_combo.addItem(p)

    def load_profile(self):
        name = self.profile_combo.currentText()
        if name.startswith("--"): return
        
        data = self.preset_manager.load_preset(name)
        if not data: return
        
        # Apply Levels
        levels = data.get("levels", {})
        for lvl_name, checked in levels.items():
            level_enum = getattr(LogLevel, lvl_name, None)
            if level_enum and level_enum in self.level_checks:
                self.level_checks[level_enum].setChecked(checked)
                
        # Apply Text Filters
        if "tags" in data and data["tags"]:
            self.txt_tag_filter.setText(data["tags"][0]) 
        else:
            self.txt_tag_filter.clear()
            
        if "keywords" in data and data["keywords"]:
            self.txt_kw_filter.setText(data["keywords"][0])
        else:
            self.txt_kw_filter.clear()
            
        QMessageBox.information(self, "Profile Loaded", f"Loaded profile: {name}")

    def save_profile(self):
        name, ok = QInputDialog.getText(self, "Save Profile", "Profile Name:")
        if ok and name:
            data = {
                "levels": {lvl.name: cb.isChecked() for lvl, cb in self.level_checks.items()},
                "tags": [self.txt_tag_filter.text()] if self.txt_tag_filter.text() else [],
                "keywords": [self.txt_kw_filter.text()] if self.txt_kw_filter.text() else []
            }
            if self.preset_manager.save_preset(name, data):
                 self.refresh_profiles()
                 self.profile_combo.setCurrentText(name)
                 QMessageBox.information(self, "Success", "Profile saved.")

    def set_levels(self, state: bool):
        for cb in self.level_checks.values():
            cb.setChecked(state)

    def refresh_filters(self):
        """Apply filters to model via Proxy"""
        # 1. Levels
        selected_levels = {lvl for lvl, cb in self.level_checks.items() if cb.isChecked()}
        self.proxy_model.set_level_filter(selected_levels)
        
        # 2. Tag
        tag = self.txt_tag_filter.text()
        self.proxy_model.set_tag_filter(tag)
        
        # 3. Keyword
        kw = self.txt_kw_filter.text()
        self.proxy_model.set_keyword_filter(kw)
        
        # scroll to bottom if auto-scroll is on?
        if self.log_view.auto_scroll:
            self.log_view.scrollToBottom()

    def on_new_logs(self, lines: List[str]):
        if self.is_paused:
            self.paused_logs_buffer.extend(lines)
            return

        entries = self.log_parser.parse_batch(lines)
        if entries:
            self.all_log_entries.extend(entries)
            self.log_model.add_entries(entries)
            self.analyzer.update_statistics(entries)
            self.update_stats_ui()
            
            # Update Timeline
            self.timeline.update_logs(self.all_log_entries)

    def update_stats_ui(self):
        stats = self.analyzer.get_summary_stats()
        self.card_total.set_value(f"{stats['total_logs']:,}")
        self.card_errors.set_value(f"{stats['level_breakdown'].get('E', 0) + stats['level_breakdown'].get('F', 0)}")
        self.card_rate.set_value(f"{stats['logs_per_second_current']:.1f}")
        
        # Format duration as HH:MM:SS
        duration_seconds = int(stats['session_duration_seconds'])
        hours = duration_seconds // 3600
        minutes = (duration_seconds % 3600) // 60
        seconds = duration_seconds % 60
        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.card_duration.set_value(duration_str)
        
        # Sidebar
        self.lbl_log_count.setText(f"Logs: {stats['total_logs']:,}")
        self.lbl_error_count.setText(f"Errors: {stats['level_breakdown'].get('E', 0)}")

        # Update Lists
        self.update_top_list(self.list_top_tags, stats['top_tags'])
        self.update_top_list(self.list_top_errors, stats['top_errors'])

    def update_top_list(self, widget: QTextEdit, data: dict):
        text = ""
        for key, count in list(data.items())[:10]:
            text += f"{count:4d} | {key}\n"
        widget.setPlainText(text)

    def update_device_list(self):
        self.device_combo.clear()
        devices = self.adb_utils.get_connected_devices()
        for d in devices:
            self.device_combo.addItem(str(d))
            
    def on_device_selected(self):
        text = self.device_combo.currentText()
        if text:
            # Simple parsing of serial
            self.current_device = text.split()[0] 
            
    def check_connection_health(self):
        if not self.adb_utils.test_device_connection(self.current_device):
            self.stop_monitoring()
            self.status_indicator.setText("Disconnected")
            self.status_indicator.setStyleSheet(f"color: {Theme.ERROR}; font-weight: bold;")
            QMessageBox.critical(self, "Connection Lost", "Device disconnected.")

    def clear_display(self):
        self.log_model.clear()
        self.all_log_entries.clear()
        self.analyzer.reset()
        self.update_stats_ui()
        self.timeline.update_logs([]) 

    def on_search_changed(self, text):
        self.proxy_model.set_search_filter(text)
        if self.log_view.auto_scroll:
            self.log_view.scrollToBottom()
    
    def on_filter_by_tag(self, tag: str):
        """Handle filter by tag request from context menu"""
        self.txt_tag_filter.setText(tag)
        # refresh_filters is automatically called via textChanged signal
        
    def on_exclude_tag(self, tag: str):
        """Handle exclude tag request from context menu"""
        self.proxy_model.add_excluded_tag(tag)
        self.update_active_filters_display()
        if self.log_view.auto_scroll:
            self.log_view.scrollToBottom()
    
    def on_filter_by_pid(self, pid: int):
        """Handle filter by PID request from context menu"""
        self.proxy_model.set_pid_filter(pid)
        self.update_active_filters_display()
        if self.log_view.auto_scroll:
            self.log_view.scrollToBottom()
    
    def clear_pid_filter(self):
        """Clear the PID filter"""
        self.proxy_model.set_pid_filter(None)
        self.update_active_filters_display()
        
    def clear_excluded_tags(self):
        """Clear all excluded tags"""
        self.proxy_model.clear_excluded_tags()
        self.update_active_filters_display()
    
    def update_active_filters_display(self):
        """Update the active filters display"""
        # PID Filter
        if self.proxy_model.filter_pid is not None:
            self.lbl_pid_filter.setText(f"PID Filter: {self.proxy_model.filter_pid}")
            self.btn_clear_pid.setEnabled(True)
        else:
            self.lbl_pid_filter.setText("PID Filter: None")
            self.btn_clear_pid.setEnabled(False)
        
        # Excluded Tags
        if self.proxy_model.filter_excluded_tags:
            tags_str = ", ".join(sorted(self.proxy_model.filter_excluded_tags))
            if len(tags_str) > 50:
                tags_str = tags_str[:47] + "..."
            self.lbl_excluded_tags.setText(f"Excluded Tags: {tags_str}")
            self.btn_clear_excluded.setEnabled(True)
        else:
            self.lbl_excluded_tags.setText("Excluded Tags: None")
            self.btn_clear_excluded.setEnabled(False)

    def show_about(self):
        QMessageBox.about(self, "About", "Android Log Monitor Pro\n\nA professional tool for Android debugging.")
        
    def closeEvent(self, event):
        self.stop_monitoring()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = AndroidLogMonitor()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
