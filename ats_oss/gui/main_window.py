import requests
from PyQt6.QtWidgets import (
    QMainWindow, QLabel, QVBoxLayout, QWidget, QTabWidget, QTreeWidget,
    QTreeWidgetItem, QLineEdit, QPushButton, QMessageBox, QFormLayout, QTextEdit,
    QSplitter, QFileDialog, QHBoxLayout, QAbstractItemView, QComboBox
)
from PyQt6.QtCore import QTimer, Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ATS-OSS Control")
        self.setGeometry(100, 100, 800, 600)

        # Create the tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create the Monitor tab
        self.monitor_tab = QWidget()
        self.tabs.addTab(self.monitor_tab, "Monitor")
        self.setup_monitor_tab()

        # Create the Submit tab
        self.submit_tab = QWidget()
        self.tabs.addTab(self.submit_tab, "Submit")
        self.setup_submit_tab()

        # Status bar for connection status
        self.status_label = QLabel("Connecting to server...")
        self.statusBar().addWidget(self.status_label)

        # Server status check timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_server_status)
        self.timer.start(5000)  # Check every 5 seconds
        self.check_server_status()

    def setup_monitor_tab(self):
        """Sets up the layout and widgets for the Monitor tab."""
        layout = QVBoxLayout(self.monitor_tab)
        splitter = QSplitter(Qt.Orientation.Vertical)

        self.workflow_tree = QTreeWidget()
        self.workflow_tree.setColumnCount(4)
        self.workflow_tree.setHeaderLabels(["ID / Name", "Created At", "Started At", "Finished At"])
        self.workflow_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        splitter.addWidget(self.workflow_tree)

        self.workflow_details = QTextEdit()
        self.workflow_details.setReadOnly(True)
        splitter.addWidget(self.workflow_details)

        self.remove_button = QPushButton("Remove Selected Completed Job(s)")

        layout.addWidget(splitter)
        layout.addWidget(self.remove_button)

        self.workflow_tree.itemSelectionChanged.connect(self.display_workflow_details)
        self.remove_button.clicked.connect(self.remove_selected_workflow)

    def display_workflow_details(self):
        """Fetches and displays the details for the selected workflow."""
        selected_items = self.workflow_tree.selectedItems()
        if not selected_items:
            return

        # The UUID is stored in the first column (index 0) of the selected item
        wfuuid = selected_items[0].text(0)

        # Ignore clicks on the category headers
        if not wfuuid:
            return

        try:
            response = requests.get(f"http://127.0.0.1:8650/workflows/getWorkflowStatus?wfuuid={wfuuid}")
            if response.status_code == 200:
                import json
                details = response.json()

                output_uri = details.get("output_uri")
                display_text = json.dumps(details, indent=2)

                if output_uri:
                    header = f"--- Output File ---\n{output_uri}\n\n--- Full Details ---\n"
                    display_text = header + display_text

                self.workflow_details.setText(display_text)
            else:
                self.workflow_details.setText(f"Error fetching details: {response.text}")
        except requests.exceptions.RequestException as e:
            self.workflow_details.setText(f"Connection error: {e}")

    def refresh_workflow_list(self):
        """Fetches the workflow list and updates the categorized tree."""
        try:
            response = requests.get("http://127.0.0.1:8650/workflows/getWorkflowList")
            if response.status_code == 200:
                workflows = response.json()
                self.workflow_tree.clear()

                state_map = {
                    0: "Queued", 1: "Running", 2: "Completed", 3: "Failed", 4: "Cancelled"
                }

                # Create top-level items for each category
                categories = {name: QTreeWidgetItem(self.workflow_tree, [name]) for name in state_map.values()}

                for wf in workflows:
                    state_str = state_map.get(wf.get("state"), "Unknown")
                    parent_item = categories.get(state_str)

                    if parent_item:
                        # Create a child item for the workflow
                        child_item = QTreeWidgetItem(parent_item)
                        child_item.setText(0, wf.get("id"))
                        child_item.setText(1, wf.get("created_at"))
                        child_item.setText(2, wf.get("started_at"))
                        child_item.setText(3, wf.get("finished_at"))

                # Expand all categories to be visible
                self.workflow_tree.expandAll()
            else:
                print(f"Failed to fetch workflow list: {response.status_code}")
        except requests.exceptions.ConnectionError:
            pass

    def setup_submit_tab(self):
        """Sets up the layout and widgets for the Submit tab."""
        layout = QFormLayout(self.submit_tab)

        self.template_combo = QComboBox()
        layout.addRow("Workflow Template:", self.template_combo)
        self.populate_workflows()

        # Create a horizontal layout for the file input and browse button
        file_input_layout = QHBoxLayout()
        self.input_uri_input = QLineEdit("path/to/your/audio.wav")
        self.browse_button = QPushButton("Browse...")
        file_input_layout.addWidget(self.input_uri_input)
        file_input_layout.addWidget(self.browse_button)
        layout.addRow("Input File URI:", file_input_layout)

        # --- Dynamic Transcode Parameters ---
        self.transcode_params_widget = QWidget()
        transcode_layout = QFormLayout(self.transcode_params_widget)

        self.format_combo = QComboBox()
        self.format_combo.addItems(["wav", "flac", "mp3", "aac", "opus"])
        self.sample_rate_input = QLineEdit("48000")
        self.bit_depth_input = QLineEdit("24")
        self.bitrate_input = QLineEdit("320k")

        transcode_layout.addRow("Format:", self.format_combo)
        transcode_layout.addRow("Sample Rate:", self.sample_rate_input)
        self.bit_depth_row = transcode_layout.addRow("Bit Depth:", self.bit_depth_input)
        self.bitrate_row = transcode_layout.addRow("Bitrate:", self.bitrate_input)

        layout.addRow(self.transcode_params_widget)
        self.transcode_params_widget.setVisible(False) # Hidden by default

        self.submit_button = QPushButton("Submit Workflow")
        layout.addRow(self.submit_button)

        self.browse_button.clicked.connect(self.browse_file)
        self.submit_button.clicked.connect(self.submit_workflow)
        self.template_combo.currentTextChanged.connect(self.on_workflow_selected)
        self.format_combo.currentTextChanged.connect(self.on_format_selected)

        # Initial check to set the correct visibility
        self.on_workflow_selected(self.template_combo.currentText())

    def on_workflow_selected(self, workflow_name):
        """Shows or hides the entire transcode parameter box."""
        is_transcode = "transcode" in workflow_name.lower()
        self.transcode_params_widget.setVisible(is_transcode)
        if is_transcode:
            # When the transcode box becomes visible, also update the format-specific fields
            self.on_format_selected(self.format_combo.currentText())

    def on_format_selected(self, format_name):
        """Shows or hides format-specific fields like bitrate or bit depth."""
        lossy_formats = ["mp3", "aac", "opus"]
        is_lossy = format_name.lower() in lossy_formats

        # QFormLayout manages the visibility of the entire row.
        # We need to get the parent QLayout object to show/hide rows.
        # It's cleaner to toggle the widgets themselves.
        self.bitrate_input.setVisible(is_lossy)
        self.bit_depth_input.setVisible(not is_lossy)

        # We also need to hide the labels
        self.transcode_params_widget.layout().labelForField(self.bitrate_input).setVisible(is_lossy)
        self.transcode_params_widget.layout().labelForField(self.bit_depth_input).setVisible(not is_lossy)

    def populate_workflows(self):
        """Scans the workflows directory and populates the dropdown."""
        from ats_oss.config import settings
        import os
        try:
            workflow_files = [f for f in os.listdir(settings.workflows_dir) if f.endswith('.yaml')]
            # Get the name without the extension
            workflow_names = [os.path.splitext(f)[0] for f in workflow_files]
            self.template_combo.addItems(workflow_names)
        except FileNotFoundError:
            QMessageBox.warning(self, "Config Error", "Workflows directory not found.")

    def remove_selected_workflow(self):
        """Removes all selected, completed workflows from the system."""
        selected_items = self.workflow_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select one or more workflows to remove.")
            return

        workflows_to_remove = []
        for item in selected_items:
            wfuuid = item.text(0)
            # Ignore category headers
            if not wfuuid:
                continue

            # Check if the workflow is in a removable state
            parent = item.parent()
            if parent and parent.text(0) in ["Completed", "Failed", "Cancelled"]:
                workflows_to_remove.append(wfuuid)

        if not workflows_to_remove:
            QMessageBox.warning(self, "State Error", "None of the selected workflows are in a removable state (Completed, Failed, or Cancelled).")
            return

        removed_count = 0
        errors = []
        for wfuuid in workflows_to_remove:
            try:
                response = requests.delete(f"http://127.0.0.1:8650/workflows/removeCompletedWorkflow?wfuuid={wfuuid}")
                if response.status_code == 204:
                    removed_count += 1
                else:
                    errors.append(f"{wfuuid}: {response.text}")
            except requests.exceptions.RequestException as e:
                errors.append(f"{wfuuid}: Connection Error - {e}")

        # Display a summary message
        if removed_count > 0:
            QMessageBox.information(self, "Success", f"{removed_count} workflow(s) removed successfully.")

        if errors:
            error_details = "\n".join(errors)
            QMessageBox.critical(self, "Error", f"Some workflows could not be removed:\n{error_details}")

        self.refresh_workflow_list()
        self.workflow_details.clear()

    def browse_file(self):
        """Opens a file dialog to select an audio file."""
        options = QFileDialog.Option.DontUseNativeDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select an Audio File",
            "", # Start directory
            "Audio Files (*.wav *.mp3 *.flac *.aac);;All Files (*)",
            options=options
        )
        if file_path:
            self.input_uri_input.setText(file_path)

    def submit_workflow(self):
        """Handles the submission of a new workflow."""
        template_name = self.template_combo.currentText()
        input_uri = self.input_uri_input.text()

        if not template_name or not input_uri:
            QMessageBox.warning(self, "Input Error", "Both fields are required.")
            return

        params = {}
        if "transcode" in template_name.lower():
            format_name = self.format_combo.currentText()
            params = {
                "format": format_name,
                "sample_rate": int(self.sample_rate_input.text()),
            }
            if format_name.lower() in ["mp3", "aac", "opus"]:
                params["bitrate"] = self.bitrate_input.text()
            else:
                params["bit_depth"] = int(self.bit_depth_input.text()) if self.bit_depth_input.text() else None

        payload = {
            "template_name": template_name,
            "input_uri": input_uri,
            "params": params,
        }
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(
                "http://127.0.0.1:8650/workflows/submitWorkflow",
                json=payload,
                headers=headers,
            )
            if response.status_code == 200:
                QMessageBox.information(self, "Success", "Workflow submitted successfully.")
                self.refresh_workflow_list()  # Refresh the monitor tab
                self.tabs.setCurrentWidget(self.monitor_tab) # Switch to monitor tab
            else:
                QMessageBox.critical(self, "Error", f"Submission failed: {response.text}")
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect to the server: {e}")

    def check_server_status(self):
        try:
            response = requests.get("http://127.0.0.1:8650/healthz")
            if response.status_code == 200 and response.json().get("status") == "ok":
                self.status_label.setText("Connected to server.")
                self.refresh_workflow_list()
            else:
                self.status_label.setText(f"Server connection failed. Status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.status_label.setText("Server not found. Is it running?")
