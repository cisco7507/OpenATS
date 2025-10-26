import requests
from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ATS-OSS Control")
        self.setGeometry(100, 100, 400, 200)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.status_label = QLabel("Connecting to server...")
        self.layout.addWidget(self.status_label)

        self.timer = QTimer()
        self.timer.timeout.connect(self.check_server_status)
        self.timer.start(5000)  # Check every 5 seconds
        self.check_server_status()

    def check_server_status(self):
        try:
            response = requests.get("http://127.0.0.1:8650/healthz")
            if response.status_code == 200 and response.json().get("status") == "ok":
                self.status_label.setText("Connected to server.")
            else:
                self.status_label.setText("Server connection failed.")
        except requests.exceptions.ConnectionError:
            self.status_label.setText("Server not found.")
