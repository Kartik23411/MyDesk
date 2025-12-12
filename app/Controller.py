# To coordinate between the GUI and Networking
import threading
from PySide6.QtCore import QObject, Signal, Slot
from common.config_manager import ConfigManager
from common.constants import DEFAULT_HOST, DEFAULT_PORT

class AppController(QObject):

    # signals for the GUI update
    connection_estabilished = Signal(str) # remote address
    connection_lost = Signal()
    frame_ready = Signal(object)
    status_update = Signal(str)

    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.current_mode = None
        self.is_connected = False

        self.server_thread = None
        self.client_thread = None

    def start_host_mode(self):

        if self.server_thread and self.server_thread.is_alive():
            print("Server is already running.")
            return
        
        self.current_mode = 'host'
        self.status_update.emit("Starting server...")
        
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
    
    def start_viewer_mode(self, remote_address, pin):

        if self.client_thread and self.client_thread.is_alive():
            print("Client is already running.")
            return
        
        self.current_mode = 'viewer'
        self.status_update.emit(f"Connecting to {remote_address}...")

        self.client_thread = threading.Thread(target=self._run_client, args=(remote_address, pin), daemon=True)
        self.client_thread.start()

    def stop(self):
        self.status_update.emit("Disconnecting...")
        # TODO: Implement graceful shutdown
        self.is_connected = False
        
    def _run_server(self):
        # TODO: Import and run server.main logic here
        print("Server thread started")
        self.status_update.emit("Waiting for connections...")
        
    def _run_client(self, remote_address, pin):
        # TODO: Import and run client.main logic here
        print(f"Client thread started - connecting to {remote_address}")
        self.status_update.emit(f"Authenticating with {remote_address}...")