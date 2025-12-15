# Controller Class for the async supported client and server

import asyncio
from PySide6.QtCore import QObject, Signal
from common.config_manager import ConfigManager
from server.async_server import AsyncServer
from client.async_client import AsyncClient

class AppController(QObject):

    connection_estabilished = Signal(str)
    connection_lost = Signal()
    error_occurred = Signal(str)
    status_update = Signal(str)

    def __init__(self):
        super().__init__()
        self.config_manager  = ConfigManager()
        self.current_mode = None

        self.server=None
        self.client=None
        self.server_task=None
        self.client_task=None

    # def start_host_mode(self, on_frame_callback=None):
        
    #     if self.server_task and self.server_task.done():
    #         print("Server already running")
    #         return
        
    #     self.current_mode = 'host'
    #     self.status_update.emit("Server Starting...")
    #     pin_hash=None
        
    #     if self.config_manager.has_pin():
    #         # TODO To be Implemented
    #         pass

    #     self.server = AsyncServer(host="0.0.0.0", port="6000", pin_hash=pin_hash)
    #     self.server_task = asyncio.create_task(self._run_server())
    #     self.status_update.emit("Server started - Waiting for connections...")

    def start_host_mode(self, on_frame_callback=None):

        print("DEBUG: start_host_mode called")  # ADD THIS
        
        if self.server_task and not self.server_task.done():
            print("Server already running")
            return
        
        self.current_mode = "host"
        self.status_update.emit("Starting server...")
        
        # Get PIN hash from config
        pin_hash = None
        if self.config_manager.has_pin():
            # Note: We're not using PIN hash yet, will implement in Day 9
            pass
        
        print(f"DEBUG: Creating server on port 6000")  # ADD THIS
        
        # Create and start server
        self.server = AsyncServer(host='0.0.0.0', port=6000, pin_hash=pin_hash)
        
        # Create async task
        self.server_task = asyncio.create_task(self._run_server())
        
        print("DEBUG: Server task created")  # ADD THIS
        
        self.status_update.emit("Server started - Waiting for connections...")

    def start_viewer_mode(self, remote_address, pin, on_frame_callback):

        if self.client:
        # to disconnect the old signals associated with previous client
            try:
                self.client.frame_received.disconnect()
                self.client.connected.disconnect()
                self.client.disconnected.disconnect()
                self.client.error_occurred.disconnect()
            except:
                pass  
        
        self.client = None
    
        if self.client_task and not self.client_task.done():
            print("Client task still running, cancelling...")
            self.client_task.cancel()
            self.client_task = None
        
        self.current_mode = "viewer"
        
        # For MVP, using localhost
        # TODO: Later, query signaling server to get actual IP
        remote_host = '127.0.0.1'
        self.status_update.emit(f"Connecting to {remote_address}...")

        self.client=AsyncClient(remote_host, 6000, pin)

        # Connect Signals
        self.client.frame_received.connect(on_frame_callback)
        self.client.connected.connect(
            lambda: self.connection_estabilished.emit(remote_address)
        )
        self.client.disconnected.connect(self.connection_lost.emit)
        self.client.error_occurred.connect(self.error_occurred.emit)

        self.client_task = asyncio.create_task(self._run_client())

    async def stop(self):
        self.status_update.emit("Disconnecting...")
         
        # Stop server
        if self.server:
            await self.server.stop()
            self.server = None
            
        # Stop client
        if self.client:
            await self.client.disconnect()
            self.client = None
            
        # Cancel tasks
        if self.server_task and not self.server_task.done():
            self.server_task.cancel()
            
        if self.client_task and not self.client_task.done():
            self.client_task.cancel()
            
        self.status_update.emit("Disconnected")

    async def _run_server(self):
        try:
            await self.server.start()
        except asyncio.CancelledError:
            print("Server task cancelled")
        except Exception as e:
            print(f"Server error: {e}")
            self.error_occurred.emit(str(e))
            
    async def _run_client(self):
        try:
            await self.client.connect()
        except asyncio.CancelledError:
            print("Client task cancelled")
        except Exception as e:
            print(f"Client error: {e}")
            self.error_occurred.emit(str(e))
    
    # Client control methods (called from GUI)
    def send_mouse_move(self, x, y):
        if self.client and self.client.is_connected:
            asyncio.create_task(self.client.send_mouse_move(x, y))
            
    def send_mouse_click(self, button, action, x, y):
        if self.client and self.client.is_connected:
            asyncio.create_task(self.client.send_mouse_click(button, action, x, y))
            
    def send_key_press(self, key_str):
        if self.client and self.client.is_connected:
            asyncio.create_task(self.client.send_key_press(key_str))
            
    def send_scroll(self, x, y, delta):
        if self.client and self.client.is_connected:
            asyncio.create_task(self.client.send_scroll(x, y, delta))