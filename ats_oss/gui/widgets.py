# ats_oss/gui/widgets.py
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import pyqtSignal, Qt

class WorkflowCanvas(QTreeWidget):
    """A custom QTreeWidget that handles drag-and-drop for workflow steps."""
    itemDropped = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.viewport().setAcceptDrops(True) # Fix for macOS drag-drop issue
        self.setDragDropMode(self.DragDropMode.InternalMove)

    def dragEnterEvent(self, event):
        # Accept drops from the palette (which is another QTreeWidget)
        if event.source() and event.source().model().rowCount() > 0:
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.source() and event.source().model().rowCount() > 0:
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        # Check if the drop is from the palette
        source_palette = event.source()
        if source_palette and source_palette != self:
            item = source_palette.currentItem()
            if item and item.parent():  # Ensure it's a draggable item, not a category
                self.itemDropped.emit(item.text(0))
                event.acceptProposedAction()
                return

        # If it's an internal move, let the base class handle it
        super().dropEvent(event)
