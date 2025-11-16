from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QLineEdit, QRadioButton,
    QButtonGroup, QFrame, QStatusBar, QMenuBar, QMenu, QMessageBox
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QImage, QPixmap, QAction, QFont
import cv2
import numpy as np

class MainWindow(QMainWindow):

    frame_received = Signal(np.ndarray)
    mode_changed = Signal(str)
    connect_requested = Signal(str)
    disconnect_requested = Signal()

    def __init__(self):
        super().__init__()
        self.current_mode = "host"  # setting the host as default mode
        self.setup_ui()
        
        # Connect signals
        self.frame_received.connect(self.update_frame)

    # to initialize the UI
    def setup_ui(self):
        self.setWindowTitle("MyDesk - Access Anytime")
        self.setMinimumSize(900, 700)
        
        # for the central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # for the main box of the layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Create sections
        self.create_menu_bar()
        self.create_mode_selector(main_layout)
        self.create_host_section(main_layout)
        self.create_viewer_section(main_layout)
        self.create_display_area(main_layout)
        self.create_status_bar()
        
        
        self.update_mode_visibility()

    def create_menu_bar(self):
        menubar = self.menuBar()

        # File menu with the two actions
        file_menu = menubar.addMenu("&File")
        
        settings_action = QAction("&Settings", self)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View Menu
        view_menu = menubar.addMenu("&View")
        
        fullscreen_action = QAction("&Fullscreen", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.setCheckable(True)
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_mode_selector(self, parent_layout):
        mode_frame = QFrame()
        mode_frame.setFrameShape(QFrame.StyledPanel)
        mode_layout = QHBoxLayout(mode_frame)

        # Mode label
        mode_label = QLabel("Mode:")
        mode_label.setFont(QFont("Arial", 10, QFont.Bold))
        mode_layout.addWidget(mode_label)
        
        # Radio buttons
        self.host_radio = QRadioButton("Share My Screen")
        self.viewer_radio = QRadioButton("Access Remote PC")
        
        self.host_radio.setChecked(True)
        self.host_radio.toggled.connect(self.on_mode_changed)
        self.viewer_radio.toggled.connect(self.on_mode_changed)

        # Button group
        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.host_radio)
        self.mode_group.addButton(self.viewer_radio)
        
        mode_layout.addWidget(self.host_radio)
        mode_layout.addWidget(self.viewer_radio)
        mode_layout.addStretch()
        
        parent_layout.addWidget(mode_frame) 

    def create_host_section(self, parent_layout):
        self.host_frame = QFrame()
        self.host_frame.setFrameShape(QFrame.StyledPanel)
        self.host_frame.setStyleSheet("QFrame { background-color: #f0f0f0; }")
        
        host_layout = QVBoxLayout(self.host_frame)
        
        # Address display
        address_layout = QHBoxLayout()
        
        address_label = QLabel("Your Address:")
        address_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        self.address_display = QLabel("XXXXX-XXXXX-XXXX")
        self.address_display.setFont(QFont("Courier", 14, QFont.Bold))
        self.address_display.setStyleSheet("QLabel { color: #2196F3; }")
        
        copy_btn = QPushButton("Copy")
        copy_btn.setMaximumWidth(60)
        copy_btn.clicked.connect(self.copy_address)
        
        address_layout.addWidget(address_label)
        address_layout.addWidget(self.address_display)
        address_layout.addWidget(copy_btn)
        address_layout.addStretch()
        
        host_layout.addLayout(address_layout)
        
        # Status
        self.host_status_label = QLabel("Status: ● Waiting for connection...")
        self.host_status_label.setStyleSheet("QLabel { color: #FF9800; }")
        host_layout.addWidget(self.host_status_label)
        
        parent_layout.addWidget(self.host_frame)

    def create_viewer_section(self, parent_layout):
        self.viewer_frame = QFrame()
        self.viewer_frame.setFrameShape(QFrame.StyledPanel)
        self.viewer_frame.setStyleSheet("QFrame { background-color: #f0f0f0; }")
        
        viewer_layout = QHBoxLayout(self.viewer_frame)
        
        # Remote address input
        remote_label = QLabel("Remote Address:")
        remote_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Enter 12-character address (e.g., AB3F9-2K7-8XQM)")
        self.address_input.setFont(QFont("Courier", 11))
        self.address_input.setMaxLength(14)  
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setMinimumWidth(100)
        self.connect_btn.clicked.connect(self.on_connect_clicked)
        
        viewer_layout.addWidget(remote_label)
        viewer_layout.addWidget(self.address_input, 1)
        viewer_layout.addWidget(self.connect_btn)
        
        parent_layout.addWidget(self.viewer_frame)

    def create_display_area(self, parent_layout):
        self.display_label = QLabel()
        self.display_label.setAlignment(Qt.AlignCenter)
        self.display_label.setMinimumSize(640, 480)
        self.display_label.setStyleSheet(
            "QLabel { background-color: black; color: white; font-size: 16px; }"
        )
        self.display_label.setText("Screen of host...")
        
        parent_layout.addWidget(self.display_label, 1)

    def create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add permanent widgets
        self.connection_status = QLabel("Connection: None")
        self.fps_label = QLabel("FPS: --")
        self.ping_label = QLabel("Ping: --")
        
        self.status_bar.addWidget(self.connection_status)
        self.status_bar.addPermanentWidget(self.fps_label)
        self.status_bar.addPermanentWidget(self.ping_label)
        
        self.status_bar.showMessage("Ready")

    def on_mode_changed(self, checked):
        if not checked:  # Ignore "unchecked" events
            return
    
        # Check the button now selected
        self.current_mode = "host" if self.host_radio.isChecked() else "viewer"
        print(f"Mode changed to: {self.current_mode}")
        self.update_mode_visibility()
        self.mode_changed.emit(self.current_mode)
            
    def update_mode_visibility(self):
        is_host = self.current_mode == "host"
    
        self.host_frame.setVisible(is_host)
        self.viewer_frame.setVisible(not is_host)
        
        # To clear display on switching the mode
        self.display_label.setText(
            "Waiting for connection..." if is_host else "Enter address to connect..."
        )
        
    def on_connect_clicked(self):
        address = self.address_input.text().strip()
        if not address:
            QMessageBox.warning(self, "Invalid Address", "Please enter a remote address.")
            return
            
        self.connect_requested.emit(address)
        
    def set_address(self, address):
        self.address_display.setText(address)
        
    def copy_address(self):
        # TODO: Implement clipboard copy
        QMessageBox.information(self, "Copied", "Address copied to clipboard!")
        
    @Slot(np.ndarray)
    def update_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        
        scaled_pixmap = pixmap.scaled(
            self.display_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        self.display_label.setPixmap(scaled_pixmap)
        
    def update_connection_status(self, status, color="#4CAF50"):
        self.connection_status.setText(f"Connection: {status}")
        self.connection_status.setStyleSheet(f"QLabel {{ color: {color}; }}")
        
    def update_fps(self, fps):
        self.fps_label.setText(f"FPS: {fps}")
        
    def update_ping(self, ping_ms):
        self.ping_label.setText(f"Ping: {ping_ms}ms")
        
    def toggle_fullscreen(self, checked):
        if checked:
            self.showFullScreen()
        else:
            self.showNormal()
            
    def show_about(self):
        QMessageBox.about(
            self,
            "About MyDesk",
            "MyDesk Remote Desktop\nVersion 1.0 (MVP)\n\n"
            "A cross-platform remote desktop application."
        )