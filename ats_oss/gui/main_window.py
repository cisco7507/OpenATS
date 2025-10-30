import requests
from PyQt6.QtWidgets import (
    QMainWindow, QLabel, QVBoxLayout, QWidget, QTabWidget, QTreeWidget,
    QTreeWidgetItem, QLineEdit, QPushButton, QMessageBox, QFormLayout, QTextEdit,
    QSplitter, QFileDialog, QHBoxLayout, QAbstractItemView, QComboBox,
    QDoubleSpinBox, QSpinBox, QPlainTextEdit
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

        # Create the Composer tab
        self.composer_tab = QWidget()
        self.tabs.addTab(self.composer_tab, "Composer")
        # --- Composer Data ---
        self.global_params = {}
        self.inspector_widgets = {}
        self.setup_composer_tab()

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
        """
        Parses the selected workflow's YAML file to determine if the transcode
        parameter box should be visible.
        """
        from ats_oss.config import settings
        import yaml

        # Construct the path to the YAML file
        template_path = settings.workflows_dir / f"{workflow_name}.yaml"

        should_show_params = False
        try:
            with open(template_path, "r") as f:
                workflow_def = yaml.safe_load(f)

                # Check for the gui_options flag
                gui_options = workflow_def.get("gui_options", {})
                if not gui_options.get("hide_transcode_params", False):
                    should_show_params = True

        except (FileNotFoundError, yaml.YAMLError) as e:
            # If the file is invalid or not found, default to hiding the params
            print(f"Could not load workflow definition for '{workflow_name}': {e}")
            should_show_params = False

        self.transcode_params_widget.setVisible(should_show_params)
        if should_show_params:
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

    def submit_workflow(self, template_name=None, input_uri=None, params=None):
        """Handles the submission of a new workflow."""
        if template_name is None:
            template_name = self.template_combo.currentText()
        if input_uri is None:
            input_uri = self.input_uri_input.text()

        if not template_name or not input_uri:
            QMessageBox.warning(self, "Input Error", "Both fields are required.")
            return

        if params is None:
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

    def setup_composer_tab(self):
        """Sets up the layout and widgets for the Composer tab."""
        layout = QVBoxLayout(self.composer_tab)

        # View switcher (Radio Buttons)
        view_switcher_layout = QHBoxLayout()
        self.composer_view_radio = QPushButton("Composer View")
        self.composer_view_radio.setCheckable(True)
        self.composer_view_radio.setChecked(True)
        self.yaml_view_radio = QPushButton("YAML View")
        self.yaml_view_radio.setCheckable(True)
        view_switcher_layout.addWidget(self.composer_view_radio)
        view_switcher_layout.addWidget(self.yaml_view_radio)
        layout.addLayout(view_switcher_layout)

        # Template management buttons
        template_layout = QHBoxLayout()
        self.load_template_button = QPushButton("Load Template")
        self.save_template_button = QPushButton("Save as Template")
        self.submit_composer_button = QPushButton("Submit from Composer")
        template_layout.addWidget(self.load_template_button)
        template_layout.addWidget(self.save_template_button)
        template_layout.addWidget(self.submit_composer_button)
        layout.addLayout(template_layout)

        # Main content area
        self.composer_stack = QWidget()
        composer_stack_layout = QVBoxLayout(self.composer_stack)
        layout.addWidget(self.composer_stack)

        # --- Composer View ---
        self.composer_view = QWidget()
        composer_layout = QHBoxLayout(self.composer_view)
        composer_stack_layout.addWidget(self.composer_view)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        composer_layout.addWidget(splitter)

        # Palette (Left)
        palette_layout = QVBoxLayout()
        self.palette = QTreeWidget()
        self.palette.setHeaderLabel("Steps")
        self.add_step_button = QPushButton("Add to Workflow")
        palette_layout.addWidget(self.palette)
        palette_layout.addWidget(self.add_step_button)
        palette_widget = QWidget()
        palette_widget.setLayout(palette_layout)
        splitter.addWidget(palette_widget)

        # Canvas (Center)
        self.canvas = QTreeWidget()
        self.canvas.setHeaderLabel("Workflow")
        self.canvas.itemSelectionChanged.connect(self._on_canvas_selection_changed)

        canvas_layout = QVBoxLayout()
        self.remove_step_button = QPushButton("Remove Selected Item")
        canvas_layout.addWidget(self.canvas)
        canvas_layout.addWidget(self.remove_step_button)
        canvas_widget = QWidget()
        canvas_widget.setLayout(canvas_layout)
        splitter.addWidget(canvas_widget)

        # Inspector (Right)
        self.inspector = QWidget()
        self.inspector_layout = QFormLayout(self.inspector)
        splitter.addWidget(self.inspector)

        # --- YAML View ---
        self.yaml_view = QTextEdit()
        self.yaml_view.setPlaceholderText("YAML definition will appear here...")
        self._is_updating_yaml = False
        self.yaml_view.textChanged.connect(self._on_yaml_text_changed)
        composer_stack_layout.addWidget(self.yaml_view)
        self.yaml_view.hide()

        # Connections
        self.composer_view_radio.clicked.connect(self.show_composer_view)
        self.yaml_view_radio.clicked.connect(self.show_yaml_view)
        self.load_template_button.clicked.connect(self.load_template)
        self.save_template_button.clicked.connect(self.save_template)
        self.submit_composer_button.clicked.connect(self.submit_from_composer)
        self.add_step_button.clicked.connect(self.add_selected_step_to_canvas)
        self.remove_step_button.clicked.connect(self.remove_selected_item)

        self.populate_palette()
        self._on_canvas_selection_changed() # Initial population of inspector

    def remove_selected_item(self):
        """Removes the selected item from the canvas."""
        selected_items = self.canvas.selectedItems()
        if not selected_items:
            return

        item = selected_items[0]
        parent = item.parent() or self.canvas.invisibleRootItem()
        parent.removeChild(item)
        self.update_yaml_view()

    def add_selected_step_to_canvas(self):
        """Adds the selected step from the palette to the canvas."""
        selected_items = self.palette.selectedItems()
        if not selected_items:
            return

        item = selected_items[0]
        if item and item.parent(): # Ensure it's a step, not a category
            self.add_item_to_canvas(item.text(0))

    def submit_from_composer(self):
        """Submits the workflow currently in the composer."""
        from ats_oss.config import settings
        import tempfile, os

        self.browse_file()
        input_uri = self.input_uri_input.text()
        if not input_uri:
            QMessageBox.warning(self, "Input Error", "An input file is required.")
            return

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".yaml", dir=settings.workflows_dir) as f:
            f.write(self.yaml_view.toPlainText())
            temp_workflow_name = os.path.splitext(os.path.basename(f.name))[0]

        self.submit_workflow(template_name=temp_workflow_name, input_uri=input_uri, params={})
        os.remove(f.name)

    def load_template(self):
        """Loads a workflow template from a YAML file."""
        from ats_oss.config import settings
        options = QFileDialog.Option.DontUseNativeDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Workflow Template", str(settings.workflows_dir), "YAML Files (*.yaml)", options=options
        )
        if file_path:
            with open(file_path, "r") as f:
                self.yaml_view.setText(f.read())
            self.update_canvas_from_yaml()

    def save_template(self):
        """Saves the current workflow to a YAML file."""
        from ats_oss.config import settings
        options = QFileDialog.Option.DontUseNativeDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Workflow Template", str(settings.workflows_dir), "YAML Files (*.yaml)", options=options
        )
        if file_path:
            with open(file_path, "w") as f:
                f.write(self.yaml_view.toPlainText())

    def populate_palette(self):
        from ats_oss.core.workflow_engine import STEP_REGISTRY
        steps_category = QTreeWidgetItem(self.palette, ["Steps"])
        for step_name in sorted(STEP_REGISTRY.keys()):
            QTreeWidgetItem(steps_category, [step_name])
        control_category = QTreeWidgetItem(self.palette, ["Control Flow"])
        for block_name in ["if", "else", "parallel", "join", "set"]:
            QTreeWidgetItem(control_category, [block_name])
        self.palette.expandAll()

    def show_composer_view(self):
        self.composer_view.show(); self.yaml_view.hide()
        self.composer_view_radio.setChecked(True); self.yaml_view_radio.setChecked(False)

    def show_yaml_view(self):
        self.composer_view.hide(); self.yaml_view.show()
        self.composer_view_radio.setChecked(False); self.yaml_view_radio.setChecked(True)
        self.update_yaml_view()

    def update_canvas_from_yaml(self):
        """Parses the YAML and rebuilds the canvas tree."""
        import yaml
        self.canvas.clear()
        self.global_params = {}

        try:
            yaml_str = self.yaml_view.toPlainText()
            if not yaml_str: return
            workflow_def = yaml.safe_load(yaml_str)
            if not workflow_def: return

            self.global_params = workflow_def.get("parameters", {})
            root = self.canvas.invisibleRootItem()
            for step_dict in workflow_def.get("steps", []):
                self._dict_to_item(root, step_dict)

            self.canvas.expandAll()
            self._on_canvas_selection_changed()

        except yaml.YAMLError as e:
            QMessageBox.warning(self, "YAML Error", f"Could not parse YAML: {e}")

    def _dict_to_item(self, parent_item, step_dict):
        """Recursively converts a YAML dictionary to a canvas item, translating to the GUI's internal data model."""
        gui_data, name_for_display = {}, "unknown"

        if "type" in step_dict:
            name_for_display = step_dict["type"]
            gui_data = dict(step_dict)
        elif "if" in step_dict:
            name_for_display = "if"
            gui_data = {"type": "if", **step_dict}
        elif "set" in step_dict:
            name_for_display = "set"
            gui_data = {"type": "set", "variable": step_dict["set"], "value": step_dict.get("value")}
        elif "parallel" in step_dict:
            name_for_display = "parallel"
            gui_data = {"type": "parallel", **step_dict}
        elif "branch" in step_dict:
            name_for_display = step_dict["branch"]
            gui_data = {"type": name_for_display, "_is_branch": True, **step_dict}
            del gui_data["branch"]
        else: return None

        if gui_data.get("type") == "if" and "if" in gui_data:
            import re
            if_expr = gui_data["if"]
            lufs_pattern = re.compile(r'"\${metrics\.integrated_lufs > ([-0-9.]+) or metrics\.integrated_lufs < ([-0-9.]+)}"')
            lufs_match = lufs_pattern.match(if_expr)
            channels_pattern = re.compile(r'"\${metrics\.channels >= parameters\.min_channels_for_downmix}"')
            channels_match = channels_pattern.match(if_expr)

            if lufs_match:
                gui_data.update({"mode": "builder", "builder_kind": "integrated_lufs_out_of_range", "lufs_max": float(lufs_match.group(1)), "lufs_min": float(lufs_match.group(2))})
            elif channels_match:
                gui_data.update({"mode": "builder", "builder_kind": "channels_greater_equal"})
            else:
                gui_data.update({"mode": "raw", "expr_raw": if_expr})

        new_item = QTreeWidgetItem(parent_item, [name_for_display])
        new_item.setFlags(new_item.flags() | Qt.ItemFlag.ItemIsEditable)
        new_item.setData(0, Qt.ItemDataRole.UserRole, gui_data)

        if "then" in step_dict:
            for child in step_dict["then"]: self._dict_to_item(new_item, child)
        if "else" in step_dict:
            else_item = self._dict_to_item(new_item, {"type": "else"})
            for child in step_dict["else"]: self._dict_to_item(else_item, child)
        if "parallel" in step_dict:
            for branch in step_dict["parallel"]: self._dict_to_item(new_item, branch)
        if "steps" in step_dict:
            for child in step_dict["steps"]: self._dict_to_item(new_item, child)

        return new_item

    def update_yaml_view(self):
        """Generates YAML from the canvas and displays it."""
        import yaml
        workflow_dict = {"name": "Composed Workflow", "parameters": self.global_params, "steps": []}
        for i in range(self.canvas.topLevelItemCount()):
            item = self.canvas.topLevelItem(i)
            workflow_dict["steps"].append(self._item_to_dict(item))

        yaml.Dumper.ignore_aliases = lambda *args : True

        try:
            yaml_str = yaml.dump(workflow_dict, sort_keys=False, default_flow_style=False)
            self._is_updating_yaml = True
            self.yaml_view.setText(yaml_str)
        except Exception as e:
            self.yaml_view.setText(f"# Error generating YAML: {e}")
        finally:
            self._is_updating_yaml = False

    def _on_yaml_text_changed(self):
        """Intermediate handler to prevent update loops."""
        if not self._is_updating_yaml:
            self.update_canvas_from_yaml()

    def _item_to_dict(self, item):
        """Recursively converts a canvas item to a dictionary for canonical YAML serialization."""
        gui_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not gui_data: return {}

        result = dict(gui_data)
        step_type = result.pop("type", "unknown")

        internal_keys = ["mode", "expr_raw", "builder_kind", "lufs_min", "lufs_max", "channels_threshold", "left_token", "operator", "right_value", "preview", "_is_branch"]
        for key in internal_keys: result.pop(key, None)

        children = [self._item_to_dict(item.child(i)) for i in range(item.childCount())]

        if step_type == "if":
            then_children, else_children = [], []
            is_else_block = False
            for child in children:
                if child == {"type": "else"}:
                    is_else_block = True; continue
                if is_else_block: else_children.append(child)
                else: then_children.append(child)

            result["then"] = then_children
            if else_children: result["else"] = else_children
            final_dict = {"if": result.pop("if")}
            final_dict.update(result)
            return final_dict
        elif step_type == "set":
            final_dict = {"set": result.pop("variable")}
            if "value" in result: final_dict["value"] = result["value"]
            return final_dict
        elif step_type == "parallel":
            return {"parallel": children}
        elif gui_data.get("_is_branch"):
             return {"branch": step_type, "steps": children}
        elif step_type == "else":
            return {"type": "else"}
        else:
            result["type"] = step_type
            if children: result["steps"] = children
            return result

    def add_item_to_canvas(self, name):
        """Adds a new item with default parameters to the canvas."""
        from .step_meta import STEP_SCHEMAS
        parent = self.canvas.currentItem() or self.canvas.invisibleRootItem()
        new_item = QTreeWidgetItem(parent, [name])
        new_item.setFlags(new_item.flags() | Qt.ItemFlag.ItemIsEditable)

        # Set default data for the new item based on its schema
        data = {"type": name}
        schema = STEP_SCHEMAS.get(name, {})
        for field in schema.get("fields", []):
            if "default" in field:
                data[field["name"]] = field["default"]
        new_item.setData(0, Qt.ItemDataRole.UserRole, data)
        self.canvas.setCurrentItem(new_item)
        self.update_yaml_view()

    def _clear_inspector(self):
        """Removes all widgets from the inspector layout."""
        self.inspector_widgets = {}
        while self.inspector_layout.count():
            child = self.inspector_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _on_canvas_selection_changed(self):
        """Handles selection changes to show the correct inspector."""
        selected_items = self.canvas.selectedItems()
        if not selected_items:
            self.display_global_parameters()
        else:
            self.display_step_inspector(selected_items[0])

    def display_global_parameters(self):
        """Displays the global parameters inspector."""
        from .step_meta import GLOBAL_PARAMETERS_SCHEMA
        self._clear_inspector()
        self.inspector_layout.addRow(QLabel("<h3>Workflow Parameters</h3>"))
        for field in GLOBAL_PARAMETERS_SCHEMA:
            # Note: For global params, 'bind' acts as the 'name'
            value = self.global_params.get(field["bind"])
            def on_change(new_value, bind_key=field["bind"]):
                self.global_params[bind_key] = new_value
                self.update_yaml_view()
            self._create_widget(field, value, on_change)

    def display_step_inspector(self, item):
        """Displays the configuration options for the selected step item."""
        from .step_meta import STEP_SCHEMAS
        self._clear_inspector()
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {"type": "unknown"}
        step_type = item_data.get("type", "unknown")
        self.inspector_layout.addRow(QLabel(f"<h3>{step_type}</h3>"))
        schema = STEP_SCHEMAS.get(step_type, {})

        for field in schema.get("fields", []):
            value = item_data.get(field["name"])
            def on_change(new_value, field_name=field["name"]):
                item_data[field_name] = new_value
                item.setData(0, Qt.ItemDataRole.UserRole, item_data)
                self._update_widget_visibility(item_data)
                if step_type == "if":
                    self._update_if_preview(item, item_data)
                self.update_yaml_view()
            self._create_widget(field, value, on_change)

        self._update_widget_visibility(item_data)
        if step_type == "if":
            self._update_if_preview(item, item_data)

    def _create_widget(self, field, current_value, on_change_callback):
        """Creates and connects a widget based on a field schema."""
        label_text = field.get("label", field["name"])
        widget = None
        if field["type"] == "float":
            widget = QDoubleSpinBox()
            if "min" in field: widget.setMinimum(field["min"])
            if "max" in field: widget.setMaximum(field["max"])
            if "step" in field: widget.setSingleStep(field["step"])
            val = current_value if current_value is not None else field.get("default", 0.0)
            widget.setValue(float(val))
            widget.valueChanged.connect(on_change_callback)
        elif field["type"] == "int":
            widget = QSpinBox()
            if "min" in field: widget.setMinimum(field["min"])
            if "max" in field: widget.setMaximum(field["max"])
            val = current_value if current_value is not None else field.get("default", 0)
            widget.setValue(int(val))
            widget.valueChanged.connect(on_change_callback)
        elif field["type"] == "select":
            widget = QComboBox()
            widget.addItems(field.get("options", []))
            if current_value: widget.setCurrentText(current_value)
            widget.currentTextChanged.connect(on_change_callback)
        elif field["type"] in ["text", "textarea"]:
            widget = QLineEdit(str(current_value or '')) if field["type"] == "text" else QPlainTextEdit(str(current_value or ''))
            widget.textChanged.connect(lambda: on_change_callback(widget.text() if isinstance(widget, QLineEdit) else widget.toPlainText()))
        elif field["type"] == "preview":
            widget = QLineEdit()
            widget.setReadOnly(True)

        if widget:
            row = self.inspector_layout.addRow(label_text, widget)
            self.inspector_widgets[field["name"]] = {"widget": widget, "row": row, "field": field}

    def _update_widget_visibility(self, item_data):
        """Shows/hides inspector widgets based on 'visible_if' rules."""
        for name, info in self.inspector_widgets.items():
            is_visible = True
            if "visible_if" in info["field"]:
                condition = info["field"]["visible_if"]
                for key, values in condition.items():
                    if item_data.get(key) not in values:
                        is_visible = False
                        break
            if "visible_if_all" in info["field"]:
                condition = info["field"]["visible_if_all"]
                for key, values in condition.items():
                    if item_data.get(key) not in values:
                        is_visible = False
                        break

            info["widget"].setVisible(is_visible)
            self.inspector_layout.labelForField(info["widget"]).setVisible(is_visible)

    def _render_if_expression(self, item_data):
        """Generates the YAML 'if' expression string based on inspector state."""
        mode = item_data.get("mode")
        if mode == "raw":
            return item_data.get("expr_raw", "").strip()

        kind = item_data.get("builder_kind")
        if kind == "integrated_lufs_out_of_range":
            lufs_max = item_data.get("lufs_max", -22.0)
            lufs_min = item_data.get("lufs_min", -24.0)
            return f'"${{metrics.integrated_lufs > {lufs_max:.1f} or metrics.integrated_lufs < {lufs_min:.1f}}}"'

        if kind == "channels_greater_equal":
            return '"${metrics.channels >= parameters.min_channels_for_downmix}"'

        if kind == "custom_compare":
            left = item_data.get("left_token", "metrics.integrated_lufs")
            op = item_data.get("operator", ">")
            right = item_data.get("right_value", "0").strip()
            return f'"${{{left} {op} {right}}}"'

        return ""

    def _update_if_preview(self, item, item_data):
        """Renders and displays the 'if' expression preview."""
        if self.inspector_widgets and "preview" in self.inspector_widgets:
            preview_widget = self.inspector_widgets["preview"]["widget"]
            expression = self._render_if_expression(item_data)
            preview_widget.setText(expression)
            # Also, save the rendered expression back to the item's data for serialization
            item_data["if"] = expression
            item.setData(0, Qt.ItemDataRole.UserRole, item_data)
