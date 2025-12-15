import asyncio
import struct
import time
from turtle import width

from common.constants import (MSG_KEY_PRESS, MSG_MOUSE_CLICK, MSG_MOUSE_MOVE, MSG_SCREENSHOT, MSG_SCROLL,
                            DEFAULT_PORT, FRAME_DELAY)
from common.protocol import send_message, recv_message
from server.capture.screen_capture import ScreenCapture
from server.control.keyboard_control import KeyboardController
from server.control.mouse_control import MouseController

class AsyncServer:

    def __init__(self, host="'0.0.0.0", port=DEFAULT_PORT, pin_hash=None):
        self.host = host
        self.port = port
        self.pin_hash = pin_hash
        self.server = None
        self.is_running = False
        self.client_writer = None
        # Controller
        self.mouse_ctrl = MouseController()
        self.keyboar_ctrl = KeyboardController()
        self.screen_capture = None

    # async def start(self):
    #     self.server = await asyncio.start_server(
    #         self.handle_client,
    #         self.host,
    #         self.port
    #     )
    #     self.is_running = True
    #     addr = self.server.sockets[0].getsockname()
    #     print(f"Server running on {addr}")

    #     async with self.server:
    #         await self.server.serve_forever()

    async def start(self):
        print("DEBUG: AsyncServer.start() called")  # ADD THIS
        
        self.server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )
        
        self.is_running = True
        addr = self.server.sockets[0].getsockname()
        print(f"Server started on {addr}")
        
        async with self.server:
            await self.server.serve_forever()
    
    async def stop(self):
        self.is_running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    async def handle_client(self, reader, writer):
        # reader and writer are stream reader and writer objects

        addr = writer.get_extra_info('peername')
        print(f"Client connected: {addr}")
        self.client_writer = writer

        send_task = None
        recv_task = None

        try:
            #TODO Add Pin authentication 

            # Screen Capture
            self.screen_capture = ScreenCapture(with_cursor=True)
            self.screen_capture.start()
            # Sending and receiveing task
            send_task = asyncio.create_task(self.send_frames(writer))    
            recv_task = asyncio.create_task(self.receive_control_events(reader))
            # To wait for a task either to finish
            done, pending = await asyncio.wait(
                [send_task, recv_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            # Cancel the remanaining task so that server can reconnect freshly
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        except Exception as e:
            print(f"Client handling error: {e}")

        finally:
            print(f"Client disconnected: {addr}")
            if self.screen_capture:
                self.screen_capture.stop()  
                self.screen_capture = None
            
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass

            self.client_writer = None

    async def send_frames(self, writer):
        while self.is_running:
            try:
                jpeg_bytes, width, height = self.screen_capture.capture_frame()

                metadata = struct.pack("III", width, height, len(jpeg_bytes))
                payload = metadata + jpeg_bytes

                header = struct.pack("!BI", MSG_SCREENSHOT, len(payload))
                writer.write(header)
                writer.write(payload)
                await writer.drain()

                await asyncio.sleep(FRAME_DELAY)
            except Exception as e:
                print(f"Error sending frame {e}")
                break

    async def receive_control_events(self, reader):
        while self.is_running:
            try:
                header = await reader.readexactly(5)
                msg_type, payload_len = struct.unpack("!BI", header)

                payload = await reader.readexactly(payload_len)
                self.handle_control_events(msg_type, payload)

            except asyncio.IncompleteReadError:
                print("Client closed connection")
                break   
            except ConnectionResetError:
                print("Connection reset by the client")
                break
            except BrokenPipeError:
                print("Connection broken - Client Disconnected")
                break
            except Exception as e:
                print(f"Error receiving control event: {e}")
                break

    def handle_control_events(self, msg_type, payload):
        try:
            if msg_type == MSG_MOUSE_MOVE:
                x, y = struct.unpack('!II', payload)
                self.mouse_ctrl.move(x, y)

            elif msg_type == MSG_MOUSE_CLICK:
                button, action, x, y = struct.unpack("!BBII", payload)
                self.mouse_ctrl.click(x, y, button, action)

            elif msg_type == MSG_KEY_PRESS:
                key_str = payload.decode('utf-8')
                self.keyboard_ctrl.type_key(key_str)

            elif msg_type == MSG_SCROLL:
                x, y, delta = struct.unpack("!IIi", payload)
                self.mouse_ctrl.scroll(x, y, delta)
        except Exception as e:
            print(f"Error handling control event: {e}")

# Test function
async def test_server():
    """Test the async server."""
    server = AsyncServer(host='127.0.0.1', port=6000)
    await server.start()


if __name__ == "__main__":
    asyncio.run(test_server())