from typing import List, Optional
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QRect
from PyQt6.QtGui import QPainter, QColor, QPen
from src.log_parser import LogEntry

class TimelineWidget(QWidget):
    """Widget for displaying log timeline and selecting time ranges"""
    time_range_changed = pyqtSignal(object, object)  # start_time, end_time
    
    def __init__(self):
        super().__init__()
        self.log_entries = []
        self.start_time = None
        self.end_time = None
        self.selection_start = None
        self.selection_end = None
        self.dragging = False
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Timeline")
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)
        
        # Quick filter buttons
        btn_layout = QHBoxLayout()
        
        self.last_30sec_btn = QPushButton("Last 30 sec")
        self.last_30sec_btn.clicked.connect(lambda: self.set_quick_filter(30))
        btn_layout.addWidget(self.last_30sec_btn)
        
        self.last_1min_btn = QPushButton("Last 1 min")
        self.last_1min_btn.clicked.connect(lambda: self.set_quick_filter(60))
        btn_layout.addWidget(self.last_1min_btn)
        
        self.last_5min_btn = QPushButton("Last 5 min")
        self.last_5min_btn.clicked.connect(lambda: self.set_quick_filter(300))
        btn_layout.addWidget(self.last_5min_btn)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_selection)
        btn_layout.addWidget(self.clear_btn)
        
        layout.addLayout(btn_layout)
        
        # Timeline display area
        self.setMinimumHeight(100)
        self.setMaximumHeight(150)
        
        self.setLayout(layout)
    
    def update_logs(self, entries: List[LogEntry]):
        """Update the timeline with new log entries"""
        if not entries:
            return
        
        self.log_entries = entries
        if entries:
            self.start_time = entries[0].timestamp
            self.end_time = entries[-1].timestamp
        
        self.update()
    
    def set_quick_filter(self, seconds: int):
        """Set a quick time filter for the last N seconds"""
        if not self.log_entries or not self.end_time:
            return
        
        # Calculate start time
        start = self.end_time - timedelta(seconds=seconds)
        self.selection_start = start
        self.selection_end = self.end_time
        
        self.time_range_changed.emit(start, self.end_time)
        self.update()
    
    def clear_selection(self):
        """Clear the time range selection"""
        self.selection_start = None
        self.selection_end = None
        self.time_range_changed.emit(None, None)
        self.update()
    
    def paintEvent(self, event):
        """Paint the timeline visualization"""
        super().paintEvent(event)
        
        if not self.log_entries or not self.start_time or not self.end_time:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background
        rect = self.rect()
        painter.fillRect(rect, QColor(240, 240, 240))
        
        # Calculate time range
        total_duration = (self.end_time - self.start_time).total_seconds()
        if total_duration == 0:
            return
        
        # Draw log density histogram
        num_bins = min(100, rect.width() // 5)
        bin_width = rect.width() / num_bins
        bin_counts = [0] * num_bins
        
        for entry in self.log_entries:
            time_offset = (entry.timestamp - self.start_time).total_seconds()
            bin_index = int((time_offset / total_duration) * num_bins)
            if 0 <= bin_index < num_bins:
                bin_counts[bin_index] += 1
        
        max_count = max(bin_counts) if bin_counts else 1
        
        # Draw histogram bars
        for i, count in enumerate(bin_counts):
            if count > 0:
                bar_height = (count / max_count) * (rect.height() - 20)
                x = i * bin_width
                y = rect.height() - bar_height - 10
                painter.fillRect(int(x), int(y), int(bin_width), int(bar_height), QColor(100, 150, 200))
        
        # Draw selection overlay
        if self.selection_start and self.selection_end:
            start_offset = (self.selection_start - self.start_time).total_seconds()
            end_offset = (self.selection_end - self.start_time).total_seconds()
            
            start_x = (start_offset / total_duration) * rect.width()
            end_x = (end_offset / total_duration) * rect.width()
            
            # Draw selection rectangle
            painter.fillRect(int(start_x), 0, int(end_x - start_x), rect.height(), 
                           QColor(255, 255, 0, 100))
            
            # Draw selection borders
            pen = QPen(QColor(255, 200, 0), 2)
            painter.setPen(pen)
            painter.drawLine(int(start_x), 0, int(start_x), rect.height())
            painter.drawLine(int(end_x), 0, int(end_x), rect.height())
    
    def mousePressEvent(self, event):
        """Handle mouse press for selection"""
        if event.button() == Qt.MouseButton.LeftButton and self.start_time and self.end_time:
            self.dragging = True
            time_offset = self.get_time_from_x(event.pos().x())
            self.selection_start = time_offset
            self.selection_end = time_offset
            self.update()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for selection"""
        if self.dragging and self.start_time and self.end_time:
            time_offset = self.get_time_from_x(event.pos().x())
            self.selection_end = time_offset
            self.update()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release for selection"""
        if event.button() == Qt.MouseButton.LeftButton and self.dragging:
            self.dragging = False
            if self.selection_start and self.selection_end:
                # Ensure start is before end
                if self.selection_start > self.selection_end:
                    self.selection_start, self.selection_end = self.selection_end, self.selection_start
                self.time_range_changed.emit(self.selection_start, self.selection_end)
    
    def get_time_from_x(self, x: int) -> datetime:
        """Convert x coordinate to timestamp"""
        if not self.start_time or not self.end_time:
            return datetime.now()
        
        total_duration = (self.end_time - self.start_time).total_seconds()
        ratio = x / self.rect().width()
        offset_seconds = ratio * total_duration
        return self.start_time + timedelta(seconds=offset_seconds)
