import socket
import struct
import time
import select

from common.constants import (MSG_KEY_PRESS, MSG_MOUSE_CLICK, MSG_MOUSE_MOVE, MSG_SCREENSHOT, MSG_SCROLL,
                              DEFAULT_HOST, DEFAULT_PORT, FRAME_DELAY)
from common.protocol import send_message, recv_message
from server.capture.screen_capture import ScreenCapture
from server.control.keyboard_control import KeyboardController
from server.control.mouse_control import MouseController

def handle_control_event(msg_type, payload, keyboard_ctrl, mouse_ctrl):

    if msg_type == MSG_MOUSE_MOVE:
        x, y = struct.unpack('!II', payload)
        mouse_ctrl.move(x, y)

    elif msg_type == MSG_MOUSE_CLICK:
        button, action, x, y = struct.unpack("!BBII", payload)
        mouse_ctrl.click(x, y, button, action)

    elif msg_type == MSG_KEY_PRESS:
        key_str = payload.decode('utf-8')
        keyboard_ctrl.type_key(key_str)

    elif msg_type == MSG_SCROLL:
        x, y, delta = struct.unpack("!IIi", payload)
        mouse_ctrl.scroll(x, y, delta)

def main():
    HOST = DEFAULT_HOST  
    PORT = DEFAULT_PORT
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(1)
        print(f"Server listening on {HOST}:{PORT}")
        
        while True:
            try:
                conn, addr = server_socket.accept()
                print(f"Client connected: {addr}")

                # Controller classes initialization
                mouse_ctrl = MouseController()
                keyboard_ctrl = KeyboardController()
                
                with ScreenCapture(with_cursor=True) as capture:
                    while True:
                        # Checking for control events (non-blocking)
                        readable, _, _ = select.select([conn], [], [], 0)
                        if readable:
                            try:
                                msg_type, payload = recv_message(conn)
                                handle_control_event(msg_type, payload, keyboard_ctrl, mouse_ctrl)
                            except Exception as e:
                                print(f"Error handling control event: {e}")
                        
                        try:
                            jpeg_bytes, width, height = capture.capture_frame()
                            
                            # Packing metadata
                            metadata = struct.pack("III", width, height, len(jpeg_bytes))
                            payload = metadata + jpeg_bytes
                            
                            send_message(conn, MSG_SCREENSHOT, payload)
                            time.sleep(FRAME_DELAY)
                            
                        except (BrokenPipeError, ConnectionResetError):
                            print("Client disconnected, waiting for next...")
                            break
                            
            except (BrokenPipeError, ConnectionResetError):
                print("Connection error")
            except KeyboardInterrupt:
                print("\nShutting down server...")
                break


if __name__ == "__main__":
    main()