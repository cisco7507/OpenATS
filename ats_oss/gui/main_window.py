import requests
from PyQt6.QtWidgets import (
    QMainWindow, QLabel, QVBoxLayout, QWidget, QTabWidget, QTableWidget,
    QTableWidgetItem, QLineEdit, QPushButton, QMessageBox, QFormLayout, QTextEdit,
    QSplitter
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

        self.workflow_table = QTableWidget()
        self.workflow_table.setColumnCount(6)
        self.workflow_table.setHorizontalHeaderLabels(
            ["ID", "Name", "State", "Created At", "Started At", "Finished At"]
        )
        splitter.addWidget(self.workflow_table)

        self.workflow_details = QTextEdit()
        self.workflow_details.setReadOnly(True)
        splitter.addWidget(self.workflow_details)

        layout.addWidget(splitter)

        self.workflow_table.itemSelectionChanged.connect(self.display_workflow_details)

    def display_workflow_details(self):
        """Fetches and displays the details for the selected workflow."""
        selected_items = self.workflow_table.selectedItems()
        if not selected_items:
            return

        # Get the row of the current selection, then get the item from the first column (ID)
        selected_row = self.workflow_table.currentRow()
        id_item = self.workflow_table.item(selected_row, 0)

        if id_item is None:
            return # Should not happen if a cell is selected, but good practice

        wfuuid = id_item.text()

        try:
            response = requests.get(f"http://127.0.0.1:8650/workflows/getWorkflowStatus?wfuuid={wfuuid}")
            if response.status_code == 200:
                import json
                details = response.json()

                # Check for an output URI and highlight it
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
        """Fetches the workflow list and updates the table."""
        try:
            response = requests.get("http://127.0.0.1:8650/workflows/getWorkflowList")
            if response.status_code == 200:
                workflows = response.json()
                self.workflow_table.setRowCount(len(workflows))
                for i, wf in enumerate(workflows):
                    self.workflow_table.setItem(i, 0, QTableWidgetItem(wf.get("id")))
                    self.workflow_table.setItem(i, 1, QTableWidgetItem(wf.get("name")))
                    # A map for human-readable states
                    state_map = {0: "Queued", 1: "Running", 2: "Completed", 3: "Failed", 4: "Cancelled"}
                    state_str = state_map.get(wf.get("state"), "Unknown")
                    self.workflow_table.setItem(i, 2, QTableWidgetItem(state_str))
                    self.workflow_table.setItem(i, 3, QTableWidgetItem(wf.get("created_at")))
                    self.workflow_table.setItem(i, 4, QTableWidgetItem(wf.get("started_at")))
                    self.workflow_table.setItem(i, 5, QTableWidgetItem(wf.get("finished_at")))
            else:
                print(f"Failed to fetch workflow list: {response.status_code}")
        except requests.exceptions.ConnectionError:
            # This is handled by the main status checker, but good to be safe
            pass

    def setup_submit_tab(self):
        """Sets up the layout and widgets for the Submit tab."""
        layout = QFormLayout(self.submit_tab)

        self.template_name_input = QLineEdit("normalize_and_qc")
        self.input_uri_input = QLineEdit("path/to/your/audio.wav")
        self.submit_button = QPushButton("Submit Workflow")

        layout.addRow("Workflow Template:", self.template_name_input)
        layout.addRow("Input File URI:", self.input_uri_input)
        layout.addRow(self.submit_button)

        self.submit_button.clicked.connect(self.submit_workflow)

    def submit_workflow(self):
        """Handles the submission of a new workflow."""
        template_name = self.template_name_input.text()
        input_uri = self.input_uri_input.text()

        if not template_name or not input_uri:
            QMessageBox.warning(self, "Input Error", "Both fields are required.")
            return

        payload = {"template_name": template_name, "input_uri": input_uri}
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
