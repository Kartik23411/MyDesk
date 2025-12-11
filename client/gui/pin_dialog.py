from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class PinSetupDialog(QDialog):

    def __init__(self, parent = None):
        super().__init__(parent)
        self.pin = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("MyDesk - PIN Setup")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Set Up Your PIN")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Info text
        info_label = QLabel(
            "Create a 4-6 digit PIN to secure your remote desktop.\n"
            "You'll need this PIN when others connect to your computer."
        )
        info_label.setWordWrap(True)
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        # PIN input
        pin_layout = QVBoxLayout()
        
        pin_label = QLabel("Enter PIN:")
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.Password)
        self.pin_input.setMaxLength(6)
        self.pin_input.setPlaceholderText("4-6 digits")
        
        pin_layout.addWidget(pin_label)
        pin_layout.addWidget(self.pin_input)
        
        layout.addLayout(pin_layout)
        
        # Confirm PIN input
        confirm_layout = QVBoxLayout()
        
        confirm_label = QLabel("Confirm PIN:")
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setMaxLength(6)
        self.confirm_input.setPlaceholderText("Re-enter PIN")
        
        confirm_layout.addWidget(confirm_label)
        confirm_layout.addWidget(self.confirm_input)
        
        layout.addLayout(confirm_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("Set PIN")
        self.ok_button.clicked.connect(self.validate_and_accept)
        self.ok_button.setDefault(True)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)

    def validate_and_accept(self):
        pin = self.pin_input.text()
        confirm = self.confirm_input.text()
        
        # Validate PIN length
        if len(pin) < 4:
            QMessageBox.warning(
                self,
                "Invalid PIN",
                "PIN must be at least 4 digits long."
            )
            return
        
        # Check if PIN is numeric
        if not pin.isdigit():
            QMessageBox.warning(
                self,
                "Invalid PIN",
                "PIN must contain only numbers."
            )
            return
        
        # Check if PINs match
        if pin != confirm:
            QMessageBox.warning(
                self,
                "PIN Mismatch",
                "PINs do not match. Please try again."
            )
            self.confirm_input.clear()
            return
        
        # PIN is valid
        self.pin = pin
        self.accept()

    def get_pin(self):
        return self.pin

class PinVerifyDialog(QDialog): 
    
    def __init__(self, remote_address, parent=None):
        super().__init__(parent)
        self.remote_address = remote_address
        self.pin = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("MyDesk - Enter PIN")
        self.setModal(True)
        self.setMinimumWidth(350)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel(f"Connect to {self.remote_address}")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Info
        info_label = QLabel("Enter the PIN for this computer:")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        # PIN input
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.Password)
        self.pin_input.setMaxLength(6)
        self.pin_input.setPlaceholderText("Enter PIN")
        self.pin_input.setAlignment(Qt.AlignCenter)
        font = self.pin_input.font()
        font.setPointSize(14)
        self.pin_input.setFont(font)
        layout.addWidget(self.pin_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("Connect")
        self.ok_button.clicked.connect(self.accept_pin)
        self.ok_button.setDefault(True)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        
    def accept_pin(self):
        pin = self.pin_input.text()
        
        if not pin:
            QMessageBox.warning(
                self,
                "No PIN",
                "Please enter a PIN."
            )
            return
        
        self.pin = pin
        self.accept()
        
    def get_pin(self):
        return self.pin


# Test dialogs
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Test PIN setup dialog
    print("Testing PIN Setup Dialog...")
    setup_dialog = PinSetupDialog()
    if setup_dialog.exec() == QDialog.Accepted:
        print(f"PIN set: {setup_dialog.get_pin()}")
    else:
        print("Setup cancelled")
    
    # Test PIN verify dialog
    print("\nTesting PIN Verify Dialog...")
    verify_dialog = PinVerifyDialog("AB3F9-2K7-8XQM")
    if verify_dialog.exec() == QDialog.Accepted:
        print(f"PIN entered: {verify_dialog.get_pin()}")
    else:
        print("Verification cancelled")
    
    sys.exit()
       