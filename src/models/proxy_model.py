from PyQt6.QtCore import QSortFilterProxyModel, Qt, QModelIndex
from src.log_parser import LogLevel, LogEntry
from src.models.log_model import LogTableModel

class LogProxyModel(QSortFilterProxyModel):
    """
    Proxy model responsible for filtering and sorting log entries.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filter_levels = set() # Enabled levels
        self.filter_tag = ""
        self.filter_keyword = ""
        self.filter_search_text = ""
        self.filter_pid = None # Optional PID filtering
        self.filter_time_start = None # Optional time range start
        self.filter_time_end = None # Optional time range end
        self.filter_excluded_tags = set() # Tags to exclude
        
        # Default to all levels enabled
        for level in LogLevel:
            self.filter_levels.add(level)

    def set_level_filter(self, levels: set):
        self.filter_levels = levels
        self.invalidateFilter()

    def set_tag_filter(self, tag: str):
        self.filter_tag = tag.lower()
        self.invalidateFilter()

    def set_keyword_filter(self, keyword: str):
        self.filter_keyword = keyword.lower()
        self.invalidateFilter()
        
    def set_search_filter(self, text: str):
        self.filter_search_text = text.lower()
        self.invalidateFilter()
        
    def set_pid_filter(self, pid: int):
        self.filter_pid = pid
        self.invalidateFilter()
        
    def set_excluded_tags(self, tags: set):
        """Set tags to exclude from display"""
        self.filter_excluded_tags = tags
        self.invalidateFilter()
        
    def add_excluded_tag(self, tag: str):
        """Add a single tag to the exclusion list"""
        self.filter_excluded_tags.add(tag)
        self.invalidateFilter()
        
    def remove_excluded_tag(self, tag: str):
        """Remove a tag from the exclusion list"""
        self.filter_excluded_tags.discard(tag)
        self.invalidateFilter()
        
    def clear_excluded_tags(self):
        """Clear all excluded tags"""
        self.filter_excluded_tags.clear()
        self.invalidateFilter()
        
    def set_time_filter(self, start, end):
        """Set time range filter. Pass None for start/end to disable time filtering."""
        self.filter_time_start = start
        self.filter_time_end = end
        self.invalidateFilter()
        
    def get_entry_at(self, proxy_row: int):
        """Get the LogEntry at the given proxy row index."""
        # Map proxy row to source row
        source_index = self.mapToSource(self.index(proxy_row, 0))
        if not source_index.isValid():
            return None
            
        source_model = self.sourceModel()
        if isinstance(source_model, LogTableModel):
            return source_model.get_entry_at(source_index.row())
        return None

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        # Get the LogEntry from source model
        source_model = self.sourceModel()
        if not isinstance(source_model, LogTableModel):
            return True
        
        entry = source_model.get_entry_at(source_row)
        if not entry:
            return False
            
        # 1. Level Filter
        if entry.level not in self.filter_levels:
            return False
            
        # 2. PID Filter
        if self.filter_pid is not None and entry.process_id != self.filter_pid:
            return False
            
        # 3. Time Range Filter
        if self.filter_time_start is not None and entry.timestamp < self.filter_time_start:
            return False
        if self.filter_time_end is not None and entry.timestamp > self.filter_time_end:
            return False

        # 4. Excluded Tags Filter
        if entry.tag in self.filter_excluded_tags:
            return False

        # 5. Tag Filter (Partial match, case-insensitive)
        if self.filter_tag and self.filter_tag not in entry.tag.lower():
            return False

        # 6. Message Keyword Filter
        if self.filter_keyword and self.filter_keyword not in entry.message.lower():
            return False
            
        # 7. Global Search (Checks Tag and Message)
        if self.filter_search_text:
            search_hit = (self.filter_search_text in entry.tag.lower() or 
                          self.filter_search_text in entry.message.lower())
            if not search_hit:
                return False

        return True

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        # Default sorting by timestamp (row number)
        # Note: LogTableModel naturally adds in time order, so row number proxy is usually fine
        # But for strictly column sorting:
        source_model = self.sourceModel()
        return super().lessThan(left, right)
