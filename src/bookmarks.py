from typing import List, Dict, Any, Optional
from datetime import datetime
from PyQt6.QtCore import pyqtSignal, QObject
from src.log_parser import LogEntry

class BookmarkManager(QObject):
    bookmarks_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.bookmarks = {}  # entry_id -> bookmark_info
        self.next_id = 1

    def toggle_bookmark(self, entry: LogEntry) -> bool:
        """Toggle bookmark for a log entry. Returns True if bookmarked, False if removed."""
        entry_id = self._get_entry_id(entry)

        if entry_id in self.bookmarks:
            del self.bookmarks[entry_id]
            self.bookmarks_changed.emit()
            return False
        else:
            self.bookmarks[entry_id] = {
                'id': self.next_id,
                'entry': entry,
                'timestamp': datetime.now(),
                'note': ''
            }
            self.next_id += 1
            self.bookmarks_changed.emit()
            return True

    def is_bookmarked(self, entry: LogEntry) -> bool:
        """Check if an entry is bookmarked"""
        entry_id = self._get_entry_id(entry)
        return entry_id in self.bookmarks

    def get_bookmarks(self) -> List[Dict[str, Any]]:
        """Get all bookmarks sorted by timestamp"""
        return sorted(self.bookmarks.values(), key=lambda x: x['timestamp'])

    def remove_bookmark(self, bookmark_id: int):
        """Remove a bookmark by ID"""
        for entry_id, bookmark in self.bookmarks.items():
            if bookmark['id'] == bookmark_id:
                del self.bookmarks[entry_id]
                self.bookmarks_changed.emit()
                break

    def clear_all_bookmarks(self):
        """Clear all bookmarks"""
        self.bookmarks.clear()
        self.bookmarks_changed.emit()

    def export_bookmarks(self, entries: List[LogEntry], filename: str, format_type: str = 'txt') -> bool:
        """Export bookmarked entries"""
        bookmarked_entries = []
        for entry in entries:
            if self.is_bookmarked(entry):
                bookmarked_entries.append(entry)

        if not bookmarked_entries:
            return False

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                if format_type == 'txt':
                    f.write("Android Log Monitor - Bookmarked Logs\n")
                    f.write("=" * 50 + "\n\n")
                    for entry in bookmarked_entries:
                        timestamp_str = entry.timestamp.strftime('%m-%d %H:%M:%S.%f')[:-3]
                        line = f"{timestamp_str} {entry.process_id:5d} {entry.thread_id:5d} {entry.level.value} {entry.tag}: {entry.message}\n"
                        f.write(line)
                elif format_type == 'csv':
                    f.write("timestamp,pid,tid,level,tag,message\n")
                    for entry in bookmarked_entries:
                        timestamp_str = entry.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')
                        f.write(f"{timestamp_str},{entry.process_id},{entry.thread_id},{entry.level.value},{entry.tag},{entry.message}\n")

            return True
        except Exception as e:
            print(f"Error exporting bookmarks: {e}")
            return False

    def _get_entry_id(self, entry: LogEntry) -> str:
        """Generate a unique ID for a log entry"""
        return f"{entry.timestamp.isoformat()}_{entry.process_id}_{entry.thread_id}_{entry.tag}_{hash(entry.message)}"
