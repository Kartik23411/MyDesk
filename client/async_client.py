import asyncio
import struct
import numpy as np
import cv2
from PySide6.QtCore import QObject, Signal
from common.constants import (
    MSG_SCREENSHOT, MSG_MOUSE_MOVE, MSG_MOUSE_CLICK,
    MSG_KEY_PRESS, MSG_SCROLL, DEFAULT_PORT, MSG_AUTH, MSG_AUTH_FAIL, MSG_AUTH_SUCCESS
)
from common.ssl_helper import SSLHelper
from common.performance import PerformanceTracker

class AsyncClient(QObject):
    # Signals for the GUI
    frame_received = Signal(np.ndarray)
    connected = Signal()
    disconnected = Signal()
    error_occurred = Signal(str)
    fps_updated=Signal(float)

    def __init__(self, remote_host, remote_port=DEFAULT_PORT, pin=None, use_ssl=True):
        super().__init__()
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.pin = pin
        self.use_ssl = use_ssl
        self.reader = None
        self.writer = None
        self.is_connected = False
        self.perf_tracker = PerformanceTracker()
        self.fps_timer = None

        self.ssl_context = None
        if self.use_ssl:
            ssl_helper = SSLHelper()
            self.ssl_context = ssl_helper.get_client_ssl_context()

    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.remote_host,
                self.remote_port,
                ssl = self.ssl_context
            )

            self.is_connected = True
            ssl_status = "with SSL" if self.use_ssl else "without SSL"
            print(f"Connected to {self.remote_host}:{self.remote_port} {ssl_status}")
            self.connected.emit()

            if self.pin:
                try:

                    pin_bytes = self.pin.encode('utf-8')
                    header = struct.pack("!BI", MSG_AUTH, len(pin_bytes))
                    self.writer.write(header)
                    self.writer.write(pin_bytes)
                    await self.writer.drain()

                    response = await self.reader.readexactly(5)
                    msg_type, payload_len = struct.unpack("!BI", response)

                    if msg_type == MSG_AUTH_FAIL: 
                        print("Authentication failed - Invalid PIN")
                        self.error_occurred.emit("Invalid PIN")
                        await self.disconnect()
                        return
                    elif msg_type == MSG_AUTH_SUCCESS: 
                        print("Authentication successful")
                    else:
                        print(f"Unexpected auth response: {msg_type}")

                except Exception as e:
                    print(f"Authentication error: {e}")
                    self.error_occurred.emit(f"Authentication error: {e}")
                    await self.disconnect()
                    return

            await self.receive_frames()
        except Exception as e:
            print(f"Connection error: {e}")
            self.error_occurred.emit(str(e))
            self.is_connected = False

    async def disconnect(self):
        self.is_connected = False
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        self.disconnected.emit()

    async def receive_frames(self):
        self.start_fps_updates()
        while self.is_connected:
            try:
                header = await self.reader.readexactly(5)
                msg_type, payload_len = struct.unpack("!BI", header)
                payload = await self.reader.readexactly(payload_len)
                
                if msg_type == MSG_SCREENSHOT:
                    metadata = payload[:12]  # Extract metadata
                    width, height, data_size = struct.unpack("III", metadata)
                    jpeg_data = payload[12:]
                    
                    # Decode JPEG
                    jpeg_array = np.frombuffer(jpeg_data, dtype=np.uint8)
                    img_bgr = cv2.imdecode(jpeg_array, cv2.IMREAD_COLOR)
                    
                    # record frames
                    self.perf_tracker.record_frame()

                    # Emit frame to GUI
                    if img_bgr is not None:
                        self.frame_received.emit(img_bgr)
                    
            except asyncio.IncompleteReadError:
                print("Connection closed by server")
                break
            except Exception as e:
                print(f"Error receiving frame: {e}")
                self.error_occurred.emit(str(e))
                break
                
        self.stop_fps_updates()        
        await self.disconnect()

    async def send_mouse_move(self, x, y):

        if not self.is_connected:
            return
            
        payload = struct.pack("!II", x, y)
        await self._send_message(MSG_MOUSE_MOVE, payload)
        
    async def send_mouse_click(self, button, action, x, y):
            # button: Button number (1=left, 2=right, 3=middle)
            # action: Action (1=press, 0=release)

        if not self.is_connected:
            return
            
        payload = struct.pack("!BBII", button, action, x, y)
        await self._send_message(MSG_MOUSE_CLICK, payload)
        
    async def send_key_press(self, key_str):
        # key_str: Key string
        if not self.is_connected:
            return
            
        payload = key_str.encode('utf-8')
        await self._send_message(MSG_KEY_PRESS, payload)
        
    async def send_scroll(self, x, y, delta):
            # delta: Scroll delta

        if not self.is_connected:
            return
            
        payload = struct.pack("!IIi", x, y, delta)
        await self._send_message(MSG_SCROLL, payload)
        
    async def _send_message(self, msg_type, payload):
        if not self.writer:
            return
            
        try:
            header = struct.pack("!BI", msg_type, len(payload))
            self.writer.write(header)
            self.writer.write(payload)
            await self.writer.drain()
        except Exception as e:
            print(f"Error sending message: {e}")
            self.error_occurred.emit(str(e))

    def start_fps_updates(self):
        async def update_fps():
            while self.is_connected:
                fps = self.perf_tracker.get_fps()
                self.fps_updated.emit(fps)
                await asyncio.sleep(1.0)

        self.fps_timer = asyncio.create_task(update_fps())

    def stop_fps_updates(self):
        if self.fps_timer:
            self.fps_timer.cancel()
            self.fps_timer = None

# Test function
async def test_client():
    client = AsyncClient('127.0.0.1', 6000)
    await client.connect()


if __name__ == "__main__":
    asyncio.run(test_client())