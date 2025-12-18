import re
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from PyQt6.QtCore import pyqtSignal, QObject
from src.log_parser import LogEntry, LogLevel

class LogFilter(QObject):
    filters_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.reset_filters()

    def reset_filters(self):
        """Reset all filters to show everything"""
        self.level_filter = set()  # Empty means show all
        self.tag_filter = ""
        self.tag_regex = None
        self.keyword_filter = ""
        self.keyword_regex = None
        self.process_id_filter = None
        self.thread_id_filter = None
        self.time_start = None
        self.time_end = None
        self.exclude_tags = set()
        self.case_sensitive = False

    def set_level_filter(self, levels: Set[str]):
        """Set log level filter (empty set = show all)"""
        self.level_filter = set(LogLevel(level) for level in levels if level in [l.value for l in LogLevel])
        self.filters_changed.emit()

    def set_tag_filter(self, tag_pattern: str, use_regex: bool = False):
        """Set tag filter"""
        self.tag_filter = tag_pattern.strip()
        if use_regex and self.tag_filter:
            try:
                self.tag_regex = re.compile(self.tag_filter, re.IGNORECASE if not self.case_sensitive else 0)
            except re.error:
                self.tag_regex = None
        else:
            self.tag_regex = None
        self.filters_changed.emit()

    def set_keyword_filter(self, keyword_pattern: str, use_regex: bool = False):
        """Set keyword filter"""
        self.keyword_filter = keyword_pattern.strip()
        if use_regex and self.keyword_filter:
            try:
                flags = re.IGNORECASE if not self.case_sensitive else 0
                self.keyword_regex = re.compile(self.keyword_filter, flags)
            except re.error:
                self.keyword_regex = None
        else:
            self.keyword_regex = None
        self.filters_changed.emit()

    def set_process_filter(self, pid: Optional[int]):
        """Set process ID filter"""
        self.process_id_filter = pid

    def set_thread_filter(self, tid: Optional[int]):
        """Set thread ID filter"""
        self.thread_id_filter = tid

    def set_time_range(self, start: Optional[datetime], end: Optional[datetime]):
        """Set time range filter"""
        self.time_start = start
        self.time_end = end

    def set_exclusions(self, exclude_tags: Set[str]):
        """Set tags to exclude"""
        self.exclude_tags = exclude_tags

    def set_case_sensitive(self, sensitive: bool):
        """Set case sensitivity for text filters"""
        self.case_sensitive = sensitive
        # Recompile regexes if needed
        if self.tag_filter:
            self.set_tag_filter(self.tag_filter, self.tag_regex is not None)
        if self.keyword_filter:
            self.set_keyword_filter(self.keyword_filter, self.keyword_regex is not None)

    def apply_filters(self, entries: List[LogEntry]) -> List[LogEntry]:
        """Apply all active filters to log entries"""
        if not entries:
            return []

        filtered = []

        for entry in entries:
            if self._matches_filters(entry):
                filtered.append(entry)

        return filtered

    def _matches_filters(self, entry: LogEntry) -> bool:
        """Check if a single entry matches all active filters"""

        # Level filter
        if self.level_filter and entry.level not in self.level_filter:
            return False

        # Tag filter
        if self.tag_filter:
            if self.tag_regex:
                if not self.tag_regex.search(entry.tag):
                    return False
            else:
                flags = 0 if self.case_sensitive else re.IGNORECASE
                if not re.search(re.escape(self.tag_filter), entry.tag, flags):
                    return False

        # Exclude tags
        if entry.tag in self.exclude_tags:
            return False

        # Keyword filter
        if self.keyword_filter:
            if self.keyword_regex:
                if not self.keyword_regex.search(entry.message):
                    return False
            else:
                flags = 0 if self.case_sensitive else re.IGNORECASE
                if not re.search(re.escape(self.keyword_filter), entry.message, flags):
                    return False

        # Process ID filter
        if self.process_id_filter is not None and entry.process_id != self.process_id_filter:
            return False

        # Thread ID filter
        if self.thread_id_filter is not None and entry.thread_id != self.thread_id_filter:
            return False

        # Time range filter
        if self.time_start and entry.timestamp < self.time_start:
            return False
        if self.time_end and entry.timestamp > self.time_end:
            return False

        return True

    def get_active_filters_description(self) -> str:
        """Get human-readable description of active filters"""
        descriptions = []

        if self.level_filter:
            levels = [level.value for level in self.level_filter]
            descriptions.append(f"Levels: {', '.join(levels)}")

        if self.tag_filter:
            filter_type = "regex" if self.tag_regex else "text"
            descriptions.append(f"Tag ({filter_type}): {self.tag_filter}")

        if self.keyword_filter:
            filter_type = "regex" if self.keyword_regex else "text"
            descriptions.append(f"Keyword ({filter_type}): {self.keyword_filter}")

        if self.process_id_filter is not None:
            descriptions.append(f"Process ID: {self.process_id_filter}")

        if self.thread_id_filter is not None:
            descriptions.append(f"Thread ID: {self.thread_id_filter}")

        if self.time_start or self.time_end:
            time_desc = ""
            if self.time_start:
                time_desc += f"from {self.time_start.strftime('%H:%M:%S')}"
            if self.time_end:
                if time_desc:
                    time_desc += " "
                time_desc += f"to {self.time_end.strftime('%H:%M:%S')}"
            descriptions.append(f"Time: {time_desc}")

        if self.exclude_tags:
            descriptions.append(f"Excluding tags: {', '.join(self.exclude_tags)}")

        if not descriptions:
            return "No filters active"

        return "; ".join(descriptions)

    def save_profile(self, name: str) -> Dict[str, Any]:
        """Save current filter settings as a profile"""
        return {
            'name': name,
            'level_filter': [level.value for level in self.level_filter],
            'tag_filter': self.tag_filter,
            'tag_regex': self.tag_regex is not None,
            'keyword_filter': self.keyword_filter,
            'keyword_regex': self.keyword_regex is not None,
            'process_id_filter': self.process_id_filter,
            'thread_id_filter': self.thread_id_filter,
            'time_start': self.time_start.isoformat() if self.time_start else None,
            'time_end': self.time_end.isoformat() if self.time_end else None,
            'exclude_tags': list(self.exclude_tags),
            'case_sensitive': self.case_sensitive
        }

    def load_profile(self, profile: Dict[str, Any]):
        """Load filter settings from a profile"""
        self.reset_filters()

        if 'level_filter' in profile:
            self.set_level_filter(set(profile['level_filter']))

        if 'tag_filter' in profile:
            self.set_tag_filter(profile['tag_filter'], profile.get('tag_regex', False))

        if 'keyword_filter' in profile:
            self.set_keyword_filter(profile['keyword_filter'], profile.get('keyword_regex', False))

        if 'process_id_filter' in profile:
            self.set_process_filter(profile['process_id_filter'])

        if 'thread_id_filter' in profile:
            self.set_thread_filter(profile['thread_id_filter'])

        if 'time_start' in profile and profile['time_start']:
            self.time_start = datetime.fromisoformat(profile['time_start'])

        if 'time_end' in profile and profile['time_end']:
            self.time_end = datetime.fromisoformat(profile['time_end'])

        if 'exclude_tags' in profile:
            self.set_exclusions(set(profile['exclude_tags']))

        if 'case_sensitive' in profile:
            self.set_case_sensitive(profile['case_sensitive'])
