# ats_oss/gui/widgets.py
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import pyqtSignal, Qt, QMimeData
from PyQt6.QtGui import QDrag

class WorkflowPalette(QTreeWidget):
    """A custom QTreeWidget for the step palette that handles drag initiation."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)

    def mouseMoveEvent(self, event):
        # Manually create a QDrag object to work around a macOS Qt bug
        if event.buttons() != Qt.MouseButton.LeftButton:
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        # The text is all we need to create the new item on the canvas
        mime_data.setText(self.currentItem().text(0))
        drag.setMimeData(mime_data)

        # This initiates the drag-and-drop operation
        drag.exec(Qt.DropAction.CopyAction)

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
        # Check if the drop is from the palette (now identified by MIME data)
        if event.mimeData().hasText():
            source_widget = event.source()
            # Distinguish between a drop from the palette and an internal move
            if isinstance(source_widget, WorkflowPalette):
                step_name = event.mimeData().text()
                self.itemDropped.emit(step_name)
                event.acceptProposedAction()
                return

        # If it's an internal move, let the base class handle it
        super().dropEvent(event)
