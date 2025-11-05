import socket
import mss
import struct
import time
import select
from pynput.mouse import Controller as MouseController
import cv2
import numpy as np

HOST = "192.168.1.115"  # ip address of the server
# HOST = "localhost"
PORT = 6000  

MSG_SCREENSHOT = 0x01
MSG_MOUSE_MOVE = 0x02
MSG_MOUSE_CLICK = 0x03
MSG_KEY_PRESS = 0x04
MSG_SCROLL = 0x05

def recv_exact(sock, n):
    data = b''
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Connection Closed")
        data += chunk
    return data

# function to send header and payload
def send_message(sock, message_type, payload):
    header = struct.pack("!BI", message_type, len(payload))
    sock.sendall(header)
    sock.sendall(payload)

# function to receive message type and payload
def recv_message(sock):
    header = recv_exact(sock, 5)
    msg_type, payload_len = struct.unpack("!BI", header)
    payload = recv_exact(sock, payload_len)
    return (msg_type, payload)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serversocket: 
    serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serversocket.bind((HOST, PORT))
    serversocket.listen(1)
    print(f"Server is listening to {HOST} on {PORT}")

    while True:
        try:
            conn, addr = serversocket.accept()
            print(f"Client connected on {addr}")

            mouse = MouseController()

            with mss.mss(with_cursor=True) as sct:
                while True:
                    sct_img = sct.grab(sct.monitors[1])
                    # print(f"The width, height are {sct_img.width} * {sct_img.height} and size is {sct_img.size}")
                    # print(f"the length of the screenshot {len(sct_img.raw)}")

                    # packing the width, height and data length integers in a struct so that data of only valid length is accepted

                    readable, _, _ = select.select([conn], [], [], 0)
                    if readable:
                        try:
                            msg_type, payload = recv_message(conn)
                            if msg_type == MSG_MOUSE_MOVE:
                                x, y = struct.unpack('!II', payload)
                                mouse.position = (x, y)
                        except Exception as e:
                            print(f"Error receiving control event: {e}")
                    
                    img_array = np.frombuffer(sct_img.raw, dtype="uint8")
                    img_array = img_array.reshape(sct_img.height, sct_img.width, 4) 

                    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)

                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 75]
                    _, jpeg_data = cv2.imencode('.jpg', img_bgr, encode_param)
                    jpeg_bytes = jpeg_data.tobytes()

                    metadata = struct.pack("III", sct_img.width, sct_img.height, len(jpeg_bytes))
                    payload = metadata + jpeg_bytes

                    try: 
                        send_message(conn, MSG_SCREENSHOT, payload)
                        time.sleep(.03)
                    except (BrokenPipeError, ConnectionResetError):
                        print("[[Client Disconnected]] Waiting for other ....")
                        break
                        
        except (BrokenPipeError, ConnectionResetError):
            print("Client Disconnected")
        except KeyboardInterrupt:
            print("Shutting down the server...")
            break