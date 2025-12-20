from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QLineEdit, QRadioButton,
    QButtonGroup, QFrame, QStatusBar, QMenuBar, QMenu, QMessageBox, QDialog
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QEvent
from PySide6.QtGui import QImage, QPixmap, QAction, QFont, QKeySequence, QMouseEvent, QWheelEvent
import cv2
import numpy as np
from client.gui.pin_dialog import PinSetupDialog, PinVerifyDialog
from common.config_manager import ConfigManager
from PySide6.QtWidgets import QApplication
from app.app_controller import AppController
from client.input.mouse_handler import MouseHandler_Async
from client.input.keyboard_handler import KeyboardHandler
from client.utils.display import get_screen_size
import asyncio

class MainWindow(QMainWindow):

    frame_received = Signal(np.ndarray)
    mode_changed = Signal(str)
    connect_requested = Signal(str)
    disconnect_requested = Signal()

    def __init__(self):
        super().__init__()
        self.current_mode = "host"  # setting the host as default mode
        self.config_manager = None
        self.controller = None

        self.mouse_handler = None
        self.keyboard_handler = None

        # to get the size of display area where need to actual display
        self.displayed_pixmap_size = None
        self.setup_ui()
        
        # Connect signals
        self.frame_received.connect(self.update_frame)
        # Initialize config manaaer
        if self.initialize_config():
            self.setup_controller() # to setup the controller

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

        view_menu.addSeparator()

        session_info_action = QAction("&Session Info", self)
        session_info_action.setShortcut("Ctrl+I")
        session_info_action.triggered.connect(self.show_session_info)
        view_menu.addAction(session_info_action)

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
        copy_btn.setToolTip("Copy address (Ctrl+C)")
        
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
        
        self.reconnect_btn = QPushButton("Reconnect")
        self.reconnect_btn.setMinimumWidth(100)
        self.reconnect_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        self.reconnect_btn.clicked.connect(self.on_reconnect_clicked)
        self.reconnect_btn.hide()

        viewer_layout.addWidget(remote_label)
        viewer_layout.addWidget(self.address_input, 1)
        viewer_layout.addWidget(self.connect_btn)
        viewer_layout.addWidget(self.reconnect_btn)
        
        parent_layout.addWidget(self.viewer_frame)

    def create_display_area(self, parent_layout):
        self.display_label = QLabel()
        self.display_label.setAlignment(Qt.AlignCenter)
        self.display_label.setMinimumSize(640, 480)
        self.display_label.setStyleSheet(
            "QLabel { background-color: black; color: white; font-size: 16px; }"
        )
        self.display_label.setText("Screen of host...")

        # To enable the mouse tracking 
        self.display_label.setMouseTracking(True)
        
        parent_layout.addWidget(self.display_label, 1)

    def create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add permanent widgets
        self.connection_status = QLabel("Connection: None")
        self.quality_indicator = QLabel("Quality: --")
        self.fps_label = QLabel("FPS: --")
        self.ping_label = QLabel("Ping: --")
        
        self.status_bar.addWidget(self.connection_status)
        self.status_bar.addPermanentWidget(self.quality_indicator)
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
        address = self.address_input.text().strip().upper()
        if not address:
            QMessageBox.warning(self, "Invalid Address", "Please enter a remote address.")
            return
            
        from common.address_generator import validate_address_format
        if not validate_address_format(address):
            QMessageBox.warning(
                self,
                "Invalid Address",
                "Invalid address format.\n\n"
                "Address should be in format: XXXXX-XXX-XXXX"
            )
            return
        
        pin_dialog = PinVerifyDialog(address, self)
        if pin_dialog.exec()==QDialog.Accepted:
            pin = pin_dialog.get_pin()

            # Start viewer mode with controller
            # Pass frame handler as callback
            self.controller.start_viewer_mode(address, pin, self.frame_received.emit)

            # connnecting the fps update signal to client after the client is created
            QTimer.singleShot(200, lambda: self.connect_fps_signal())

            # Update UI
            self.connect_btn.setText("Disconnect")
            self.connect_btn.clicked.disconnect()
            self.connect_btn.clicked.connect(self.on_disconnect_clicked)
        else:
            print("Connection Cancelled")
        
    def set_address(self, address):
        self.address_display.setText(address)
        
    def copy_address(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.address_display.text())
        QMessageBox.information(self, "Copied", "Address copied to clipboard!")
        
    @Slot(np.ndarray)
    def update_frame(self, frame):

        height, width = frame.shape[:2]

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
        
        self.displayed_pixmap_size = scaled_pixmap.size()
        self.display_label.setPixmap(scaled_pixmap)

        if self.mouse_handler:
            self.mouse_handler.set_dimensions(
                width, height,  # Server screen size
                scaled_pixmap.width(), scaled_pixmap.height()  # client display window size
            )
        
    def update_connection_status(self, status, color="#4CAF50"):
        self.connection_status.setText(f"Connection: {status}")
        self.connection_status.setStyleSheet(f"QLabel {{ color: {color}; }}")
        
    def connect_fps_signal(self):
        if self.controller.client:
            self.controller.client.fps_updated.connect(self.on_fps_updated)
            print("FPS signal connected")

    def update_fps(self, fps):
        self.fps_label.setText(f"FPS: {fps}")

        if fps >= 25:
            color = "#4CAF50"  # Green - Good
        elif fps >= 15:
            color = "#FF9800"  # Orange - OK
        else:
            color = "#F44336"  # Red - Poor
        
        self.fps_label.setStyleSheet(f"QLabel {{ color: {color}; font-weight: bold; }}")

    @Slot(float)
    def on_fps_updated(self, fps):
        self.update_fps(int(fps))

        # using frame delivery time as rough latency
        if self.controller.client:
            frame_time_ms = self.controller.client.perf_tracker.get_avg_frame_time_ms()
            self.update_ping(int(frame_time_ms))

            self.update_connection_quality(int(fps), int(frame_time_ms))
        
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
            "MyDesk Remote Desktop\n"
            "Version 1.0 (MVP)\n\n"
            "A cross-platform remote desktop application.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Keyboard Shortcuts:\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "• F11 - Toggle Fullscreen\n"
            "• Ctrl+C - Copy Address (Host mode)\n"
            "• Ctrl+D - Disconnect\n"
            "• Ctrl+R - Reconnect\n"
            "• Esc - Exit Fullscreen\n"
            "• Q - Quit viewer window\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Features:\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "• SSL/TLS Encryption ✓\n"
            "• PIN Authentication ✓\n"
            "• Real-time Streaming ✓\n"
            "• Performance Monitoring ✓"
        )

    def initialize_config(self):
        self.config_manager=ConfigManager()
        address = self.config_manager.get_or_create_address()
        self.set_address(address)

        if not self.config_manager.has_pin():
            pin_dialog = PinSetupDialog(self)
            if pin_dialog.exec()==QDialog.Accepted:
                pin = pin_dialog.get_pin()
                self.config_manager.set_pin(pin)
                QMessageBox.information(
                    self,
                    "PIN Set",
                    f"Your PIN has been set successfully!\n\n"
                    f"Your Address: {address}\n\n"
                    f"Share this address with others to let them connect to your computer."
                )
            else:
                QMessageBox.warning(
                    self,
                    "PIN Required",
                    "A PIN is required to use MyDesk. Please set a PIN to continue."
                )
                self.close()
                return
        return True
    
    def setup_controller(self):
        self.controller = AppController()

        # Connect Control Signals to the UI
        self.controller.connection_estabilished.connect(self.on_connection_established)
        self.controller.status_update.connect(self.on_status_update)
        self.controller.connection_lost.connect(self.on_connection_lost)
        self.controller.error_occurred.connect(self.on_error)

        self.mode_changed.connect(self.on_mode_changed_controller)

        # automate server start on host mode entering
        if self.current_mode == "host":
            QTimer.singleShot(100, self.start_server_delayed) #starting after the 100ms of application start

    def on_status_update(self, status):
        self.status_bar.showMessage(status)

        print(f"Status {status}")
    
    def on_connection_established(self, remote_addr):
        self.update_connection_status("Connected", "#4CAF50")
        if self.current_mode == "host":
            self.host_status_label.setText("Status: ● Client connected")
            self.host_status_label.setStyleSheet("QLabel { color: #4CAF50; }")

            self.status_bar.showMessage(f"Client connected: {remote_addr}")

        elif self.current_mode == "viewer":
            self.display_label.clear()
            self.display_label.setText("") 

            # to hide reconnect and show the disconnect
            self.reconnect_btn.hide()
            self.connect_btn.show()
            self.connect_btn.setText("Disconnect")
            self.connect_btn.clicked.disconnect()
            self.connect_btn.clicked.connect(self.on_disconnect_clicked)

            QTimer.singleShot(300, self.setup_input_handlers)
            
            self.status_bar.showMessage(f"Connected to {remote_addr}")
        
    def on_connection_lost(self):

        print("DEBUG: Connection lost is called")

        self.update_connection_status("Disconnected", "#F44336")


        if self.mouse_handler:
            self.display_label.removeEventFilter(self)
            self.mouse_handler = None

        if self.keyboard_handler:
            self.keyboard_handler.stop()
            self.keyboard_handler = None

        self.update_fps(0)
        self.update_ping(0)
        self.fps_label.setStyleSheet("")

        self.quality_indicator.setText("Quality: --")
        self.quality_indicator.setStyleSheet("")

        self.display_label.clear()
        self.display_label.setText(
            "Connection lost..." if self.current_mode == "viewer" 
            else "Waiting for connection..."
        )  

        if self.current_mode == "viewer":
            self.connect_btn.hide()
            self.reconnect_btn.show()

        if self.current_mode == "host":
            self.host_status_label.setText("Status: ● Waiting for connection...")
            self.host_status_label.setStyleSheet("QLabel { color: #FF9800; }")
        
    def on_error(self, error_msg):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Connection Error", f"Error: {error_msg}")
        
    # def on_mode_changed_controller(self, mode):
    #     if mode == "host":
    #         # Start server
    #         QTimer.singleShot(100, self.controller.start_host_mode)
    #     elif mode == "viewer":
    #         # Stop any existing connections when switching to viewer
    #         if self.controller.client and self.controller.client.is_connected:
    #             asyncio.create_task(self.controller.client.disconnect())# chnge done

    def on_mode_changed_controller(self, mode):
        if mode == "host":
            # Start server if not running
            if not self.controller.server or not self.controller.server.is_running:
                QTimer.singleShot(100, self.controller.start_host_mode)
            
        elif mode == "viewer":
            # (actual connection happens on Connect button)
            pass

    def on_disconnect_clicked(self):
        asyncio.create_task(self.controller.stop())
        
        # Update UI
        self.connect_btn.setText("Connect")
        self.connect_btn.clicked.disconnect()
        self.connect_btn.clicked.connect(self.on_connect_clicked)


        self.connect_btn.hide()
        self.reconnect_btn.show()

        self.display_label.clear()
        self.display_label.setText("Enter address to connect...")

    def closeEvent(self, event):
        # Stop controller
        if self.controller:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self.controller.stop())
        
        # Stop keyboard listener if exists
        if hasattr(self, 'keyboard_handler') and self.keyboard_handler:
            self.keyboard_handler.stop()
        
        event.accept()
        
        # Force quit after a short delay
        from PySide6.QtWidgets import QApplication
        QApplication.instance().quit()

    def start_server_delayed(self):
        if self.current_mode == "host":
            self.controller.start_host_mode()

    def update_connection_quality(self, fps, ping_ms):
 
        if fps >= 25 and ping_ms < 50:
            quality = "Excellent"
            color = "#4CAF50"
            icon = "●"
        elif fps >= 20 and ping_ms < 100:
            quality = "Good"
            color = "#8BC34A"
            icon = "●"
        elif fps >= 15 and ping_ms < 150:
            quality = "Fair"
            color = "#FF9800"
            icon = "◐"
        elif fps >= 10:
            quality = "Poor"
            color = "#FF5722"
            icon = "◑"
        else:
            quality = "Bad"
            color = "#F44336"
            icon = "○"
        
        self.quality_indicator.setText(f"{icon} {quality}")
        self.quality_indicator.setStyleSheet(f"QLabel {{ color: {color}; font-weight: bold; }}")

    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()

        if (modifiers & Qt.ControlModifier) and key == Qt.Key_C: #ctrl or cmd c to copy the address
            if self.current_mode == "host":
                self.copy_address()
                event.accept()
                return
        
        elif (modifiers & Qt.ControlModifier) and key == Qt.Key_D: #ctrl or cmd d to disconnect
            if self.current_mode == "viewer" and self.controller.client:
                if self.controller.client.is_connected:
                    self.on_disconnect_clicked()
                    event.accept()
                    return
                
        elif (modifiers & Qt.ControlModifier) and key == Qt.Key_R: #ctrl or cmd r to reconnect
            if self.current_mode == "viewer":
                address = self.address_input.text().strip()
                if address:
                    self.on_connect_clicked()
                    event.accept()
                    return
                
        elif (modifiers & Qt.ControlModifier) and key == Qt.Key_I: #ctrl or cmd i to show session info
                self.show_session_info()
                event.accept()
                return
                
        elif key == Qt.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
                event.accept()
                return
            
        super().keyPressEvent(event)

    def show_session_info(self):
        if not self.controller.client or not self.controller.client.is_connected:
            QMessageBox.information(self, "Session Info", "No active session.")
            return
        
        perf = self.controller.client.perf_tracker

        duration = perf.get_session_duration()
        minutes = int(duration // 60)
        seconds = int(duration % 60)

        data_mb = perf.get_total_mb_received()
        bandwidth = perf.get_bandwidth_mbps()
        fps = perf.get_fps()
        frame_time = perf.get_avg_frame_time_ms()

        info_text = (
            f"Session Information\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Duration: {minutes}m {seconds}s\n"
            f"Frames Received: {perf.frame_count}\n"
            f"Data Received: {data_mb:.2f} MB\n"
            f"Avg Bandwidth: {bandwidth:.2f} Mbps\n\n"
            f"Performance:\n"
            f"• Current FPS: {fps:.1f}\n"
            f"• Frame Time: {frame_time:.1f} ms\n"
        )   

        QMessageBox.information(self, "Session Info", info_text)

    def on_reconnect_clicked(self):
        self.on_connect_clicked()

    def setup_input_handlers(self):

        if not self.controller.client or not self.controller: 
            print("Cannot setup input handlers - no Client")
            return
        
        mouse_callbacks = {
            "mouse_move": self.controller.send_mouse_move,
            "mouse_click": self.controller.send_mouse_click,
            "scroll": self.controller.send_scroll,
        }

        self.mouse_handler = MouseHandler_Async(mouse_callbacks)  
        self.keyboard_handler = KeyboardHandler(self.controller.send_key_press)
        
        self.keyboard_handler.start()
        self.display_label.installEventFilter(self)
        print("Input Handlers are connected")

    def eventFilter(self, obj, event):
    
        # Only handle events on display label when in viewer mode
        if obj == self.display_label and self.current_mode == "viewer" and self.mouse_handler:
            
            if self.displayed_pixmap_size:
                label_width = self.display_label.width()
                label_height = self.display_label.height()
                pixmap_width = self.displayed_pixmap_size.width()
                pixmap_height = self.displayed_pixmap_size.height()

                offset_x = (label_width - pixmap_width) // 2
                offset_y = (label_height - pixmap_height) // 2

                mouse_x = event.x() - offset_x
                mouse_y = event.y() - offset_y

                # Check if mouse is within the displayed pixmap area
                if mouse_x < 0 or mouse_x >= pixmap_width or mouse_y < 0 or mouse_y >= pixmap_height:
                    return super().eventFilter(obj, event)
            else:
                mouse_x = event.x()
                mouse_y = event.y()

            if event.type() == QEvent.MouseMove:
                self.mouse_handler.callback(cv2.EVENT_MOUSEMOVE, event.x(), event.y(), 0, None)
                return True
            
            elif event.type() == QEvent.MouseButtonPress:
                button = event.button()
                if button == Qt.LeftButton:
                    self.mouse_handler.callback(cv2.EVENT_LBUTTONDOWN, event.x(), event.y(), 0, None)
                elif button == Qt.RightButton:
                    self.mouse_handler.callback(cv2.EVENT_RBUTTONDOWN, event.x(), event.y(), 0, None)
                elif button == Qt.MiddleButton:
                    self.mouse_handler.callback(cv2.EVENT_MBUTTONDOWN, event.x(), event.y(), 0, None)
                return True
            
            elif event.type() == QEvent.MouseButtonRelease:
                button = event.button()
                if button == Qt.LeftButton:
                    self.mouse_handler.callback(cv2.EVENT_LBUTTONUP, event.x(), event.y(), 0, None)
                elif button == Qt.RightButton:
                    self.mouse_handler.callback(cv2.EVENT_RBUTTONUP, event.x(), event.y(), 0, None)
                elif button == Qt.MiddleButton:
                    self.mouse_handler.callback(cv2.EVENT_MBUTTONUP, event.x(), event.y(), 0, None)
                return True
            
            elif event.type() == QEvent.Wheel:
                delta = event.angleDelta().y()
                flags = 1 if delta > 0 else -1
                self.mouse_handler.callback(cv2.EVENT_MOUSEWHEEL, event.x(), event.y(), flags, None)
                return True
        
        # Pass event to parent
        return super().eventFilter(obj, event)