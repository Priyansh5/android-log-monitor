from typing import List, Any
from datetime import datetime
from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex, QVariant
from PyQt6.QtGui import QColor, QBrush
from src.log_parser import LogEntry, LogLevel

class LogTableModel(QAbstractTableModel):
    """
    Table model for displaying generic log entries efficiently.
    """
    
    # Column definitions
    COLUMNS = [
        "Time",
        "PID",
        "TID",
        "Level",
        "Tag",
        "Message"
    ]
    
    COL_TIME = 0
    COL_PID = 1
    COL_TID = 2
    COL_LEVEL = 3
    COL_TAG = 4
    COL_MESSAGE = 5

    # Log Level Colors (will be refined by ThemeManager later, but defaults here)
    LEVEL_COLORS = {
        LogLevel.VERBOSE: QColor("#9E9E9E"),  # Gray
        LogLevel.DEBUG: QColor("#4CAF50"),    # Green
        LogLevel.INFO: QColor("#2196F3"),     # Blue
        LogLevel.WARNING: QColor("#FFC107"),  # Orange
        LogLevel.ERROR: QColor("#F44336"),    # Red
        LogLevel.FATAL: QColor("#B71C1C"),    # Dark Red
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.entries: List[LogEntry] = []
        self._filtered_entries: List[LogEntry] = []
    
    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.entries)
    
    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.COLUMNS)
    
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self.entries)):
            return None
            
        entry = self.entries[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == self.COL_TIME:
                return entry.timestamp.strftime('%H:%M:%S.%f')[:-3]
            elif col == self.COL_PID:
                return str(entry.process_id)
            elif col == self.COL_TID:
                return str(entry.thread_id)
            elif col == self.COL_LEVEL:
                return entry.level.value
            elif col == self.COL_TAG:
                return entry.tag
            elif col == self.COL_MESSAGE:
                return entry.message
        
        elif role == Qt.ItemDataRole.ForegroundRole:
            # Colorize the whole row based on level, or just the level column?
            # For now, let's colorize the Level and Message columns
            if col in [self.COL_LEVEL, self.COL_MESSAGE, self.COL_TAG]:
                return  QBrush(self.LEVEL_COLORS.get(entry.level, QColor("white")))

        elif role == Qt.ItemDataRole.ToolTipRole:
             if col == self.COL_MESSAGE:
                 return entry.message

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if 0 <= section < len(self.COLUMNS):
                return self.COLUMNS[section]
        return None

    def set_entries(self, entries: List[LogEntry]):
        """Replace all entries with a new list"""
        self.beginResetModel()
        self.entries = entries
        self.endResetModel()

    def add_entries(self, new_entries: List[LogEntry]):
        """Append new entries efficiently"""
        if not new_entries:
            return
            
        start_row = len(self.entries)
        end_row = start_row + len(new_entries) - 1
        
        self.beginInsertRows(QModelIndex(), start_row, end_row)
        self.entries.extend(new_entries)
        self.endInsertRows()

    def clear(self):
        """Clear all entries"""
        self.beginResetModel()
        self.entries = []
        self.endResetModel()

    def get_entry_at(self, row: int) -> LogEntry:
        """Get the LogEntry object at a specific row"""
        if 0 <= row < len(self.entries):
            return self.entries[row]
        return None
