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
