from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel, QTabWidget

class SingleReplayTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.req_editor = QTextEdit()
        self.res_display = QTextEdit()
        self.res_display.setReadOnly(True)

        layout.addWidget(QLabel("Request:"))
        layout.addWidget(self.req_editor)

        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_request)
        layout.addWidget(send_btn)

        layout.addWidget(QLabel("Response:"))
        layout.addWidget(self.res_display)

    def load_request(self, req_text):
        self.req_editor.setPlainText(req_text)
        self.res_display.clear()  # clear previous response

    def send_request(self):
        # Actual sending code remains here and executes only on Send button click
        req_text = self.req_editor.toPlainText()
        # Parsing and sending logic omitted here for brevity
        # Implement as previously described
        # On error or success, set response in self.res_display

class ReplayWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        self.tab_count = 0

    def add_new_tab(self, req_text):
        self.tab_count += 1
        new_tab = SingleReplayTab()
        new_tab.load_request(req_text)
        self.tab_widget.addTab(new_tab, str(self.tab_count))
        self.tab_widget.setCurrentWidget(new_tab)
        # Note: Do NOT call send_request() here anymore
