from PyQt6.QtWidgets import QTableView, QHeaderView, QAbstractItemView, QMenu, QApplication
from PyQt6.QtCore import Qt, pyqtSignal, QModelIndex
from PyQt6.QtGui import QAction, QCursor
from models.log_model import LogTableModel
from log_parser import LogEntry

class LogTableView(QTableView):
    """
    Custom table view for displaying logs.
    Handles auto-scroll, column resizing, and context menus.
    """
    
    # Signals
    log_selected = pyqtSignal(object) # Emits LogEntry
    filter_by_tag_requested = pyqtSignal(str)
    exclude_tag_requested = pyqtSignal(str)
    filter_by_pid_requested = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.auto_scroll = True
        self.setup_ui()
        
    def setup_ui(self):
        # UI Styling/Behavior
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.verticalHeader().setVisible(False)
        
        # Performance tuning
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.setWordWrap(False) 
        
        # Context Menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def setModel(self, model):
        super().setModel(model)
        
        # Get the actual source model if it's a proxy
        from models.proxy_model import LogProxyModel
        source_model = model.sourceModel() if isinstance(model, LogProxyModel) else model
        
        if isinstance(source_model, LogTableModel):
            # Set default column widths
            header = self.horizontalHeader()
            header.setSectionResizeMode(LogTableModel.COL_TIME, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(LogTableModel.COL_PID, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(LogTableModel.COL_TID, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(LogTableModel.COL_LEVEL, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(LogTableModel.COL_TAG, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(LogTableModel.COL_MESSAGE, QHeaderView.ResizeMode.Stretch)

            self.setColumnWidth(LogTableModel.COL_TIME, 100)
            self.setColumnWidth(LogTableModel.COL_PID, 60)
            self.setColumnWidth(LogTableModel.COL_TID, 60)
            self.setColumnWidth(LogTableModel.COL_LEVEL, 40)
            self.setColumnWidth(LogTableModel.COL_TAG, 150)
            
            # Connect signals if needed (e.g., rowsInserted for auto-scroll)
            source_model.rowsInserted.connect(self.on_rows_inserted)

    def on_rows_inserted(self, parent, first, last):
        if self.auto_scroll:
            self.scrollToBottom()

    def set_auto_scroll(self, enabled: bool):
        self.auto_scroll = enabled
        if enabled:
            self.scrollToBottom()
            
    def get_selected_entry(self) -> LogEntry:
        indexes = self.selectedIndexes()
        if indexes:
            # Get the row of the first selected item
            row = indexes[0].row()
            return self.model().get_entry_at(row)
        return None

    def show_context_menu(self, pos):
        index = self.indexAt(pos)
        if not index.isValid():
            return
            
        entry = self.model().get_entry_at(index.row())
        if not entry:
            return

        menu = QMenu(self)
        
        # Copy Actions
        copy_msg_action = menu.addAction("Copy Message")
        copy_msg_action.triggered.connect(lambda: QApplication.clipboard().setText(entry.message))
        
        copy_line_action = menu.addAction("Copy Full Line")
        copy_line_action.triggered.connect(lambda: QApplication.clipboard().setText(entry.raw_line))
        
        menu.addSeparator()
        
        # Filter Actions
        filter_tag_action = menu.addAction(f"Filter by Tag: {entry.tag}")
        filter_tag_action.triggered.connect(lambda: self.filter_by_tag_requested.emit(entry.tag))
        
        exclude_tag_action = menu.addAction(f"Exclude Tag: {entry.tag}")
        exclude_tag_action.triggered.connect(lambda: self.exclude_tag_requested.emit(entry.tag))
        
        filter_pid_action = menu.addAction(f"Filter by PID: {entry.process_id}")
        filter_pid_action.triggered.connect(lambda: self.filter_by_pid_requested.emit(entry.process_id))

        menu.exec(QCursor.pos())
