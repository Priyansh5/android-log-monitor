import re
from typing import List, Dict, Any, Optional, Tuple
from PyQt6.QtCore import pyqtSignal, QObject, QTimer, QRegularExpression
from PyQt6.QtWidgets import QPlainTextEdit
from PyQt6.QtGui import QTextCursor, QColor, QTextCharFormat
from src.log_parser import LogEntry

class LogSearch(QObject):
    search_results_changed = pyqtSignal(list)  # List of (line_number, match_start, match_end)

    def __init__(self, text_widget: QPlainTextEdit):
        super().__init__()
        self.text_widget = text_widget
        self.search_term = ""
        self.use_regex = False
        self.case_sensitive = False
        self.current_match_index = -1
        self.matches = []  # List of (line_number, match_start, match_end, match_text)
        self.highlight_format = QTextCharFormat()
        self.highlight_format.setBackground(QColor("#FFFF00"))  # Yellow highlight

        # Debounce timer for search input
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)

    def set_search_term(self, term: str, use_regex: bool = False, case_sensitive: bool = False):
        """Set the search term and options"""
        self.search_term = term.strip()
        self.use_regex = use_regex
        self.case_sensitive = case_sensitive

        if self.search_term:
            self.search_timer.start(300)  # 300ms debounce
        else:
            self.clear_highlights()

    def _perform_search(self):
        """Perform the actual search"""
        self.clear_highlights()
        self.matches = []
        self.current_match_index = -1

        if not self.search_term:
            self.search_results_changed.emit([])
            return

        try:
            # Create QRegularExpression for Qt search
            if self.use_regex:
                pattern_str = self.search_term
            else:
                pattern_str = re.escape(self.search_term)

            pattern = QRegularExpression(pattern_str)
            if not self.case_sensitive:
                pattern.setPatternOptions(QRegularExpression.PatternOption.CaseInsensitiveOption)

            # Search through all text
            cursor = QTextCursor(self.text_widget.document())
            cursor.movePosition(QTextCursor.MoveOperation.Start)

            while True:
                cursor = self.text_widget.document().find(pattern, cursor)
                if cursor.isNull():
                    break

                # Get match details
                match_start = cursor.selectionStart()
                match_end = cursor.selectionEnd()
                match_text = cursor.selectedText()

                # Find line number
                block = cursor.block()
                line_number = block.blockNumber() + 1

                self.matches.append((line_number, match_start, match_end, match_text))

                # Apply highlight
                cursor.setCharFormat(self.highlight_format)

        except Exception:
            # Invalid regex or other error, don't highlight
            pass

        self.search_results_changed.emit(self.matches)

    def next_match(self) -> bool:
        """Jump to next match. Returns True if found."""
        if not self.matches:
            return False

        self.current_match_index = (self.current_match_index + 1) % len(self.matches)
        self._jump_to_match(self.current_match_index)
        return True

    def previous_match(self) -> bool:
        """Jump to previous match. Returns True if found."""
        if not self.matches:
            return False

        self.current_match_index = (self.current_match_index - 1) % len(self.matches)
        self._jump_to_match(self.current_match_index)
        return True

    def _jump_to_match(self, index: int):
        """Jump to a specific match"""
        if 0 <= index < len(self.matches):
            line_number, match_start, match_end, match_text = self.matches[index]

            # Create cursor at match position
            cursor = QTextCursor(self.text_widget.document())
            cursor.setPosition(match_start)
            cursor.setPosition(match_end, QTextCursor.MoveMode.KeepAnchor)

            # Scroll to match and select it
            self.text_widget.setTextCursor(cursor)
            self.text_widget.centerCursor()

    def clear_highlights(self):
        """Clear all search highlights"""
        # Reset format for entire document
        cursor = QTextCursor(self.text_widget.document())
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        cursor.setCharFormat(QTextCharFormat())  # Reset to default format

        self.matches = []
        self.current_match_index = -1
        self.search_results_changed.emit([])

    def jump_to_timestamp(self, timestamp_str: str) -> bool:
        """Jump to a specific timestamp. Format: MM-DD HH:MM:SS or similar"""
        try:
            # Try to find timestamp in text using QRegularExpression
            pattern = QRegularExpression(re.escape(timestamp_str))
            cursor = QTextCursor(self.text_widget.document())
            cursor = self.text_widget.document().find(pattern, cursor)

            if not cursor.isNull():
                self.text_widget.setTextCursor(cursor)
                self.text_widget.centerCursor()
                return True
        except:
            pass
        return False

    def get_match_count(self) -> int:
        """Get total number of matches"""
        return len(self.matches)

    def get_current_match_index(self) -> int:
        """Get current match index (0-based)"""
        return self.current_match_index
