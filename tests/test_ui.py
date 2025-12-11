import sys
from PySide6.QtWidgets import QApplication
from client.gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    
    # Create and show window
    window = MainWindow()
    
    # Don't set address manually anymore - it will load from config
    # window.set_address("AB3F9-2K7-8XQM")  # Remove this line
    
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()