import socket
import struct
import cv2
import numpy as np

HOST = "localhost"  # The server's hostname or IP address
PORT = 6000  # The port used by the server

# Message Constants
MSG_SCREENSHOT = 0x01
MSG_MOUSE_MOVE = 0x02
MSG_MOUSE_CLICK = 0x03
MSG_KEY_PRESS = 0x04
MSG_SCROLL = 0x05

# helper function to receivce data of exact length
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

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientsocket:
    clientsocket.connect((HOST, PORT))
    print("Connected to the sever")
    
    while True: 
        msg_type, payload = recv_message(clientsocket)
        
        if(msg_type==MSG_SCREENSHOT):
            metadata = payload[:12]
            width, height, data_size = struct.unpack("III", metadata)
            raw_data = payload[12:]
            
            img_array = np.frombuffer(raw_data, dtype=np.uint8)
            img_array = img_array.reshape(height, width, 4)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)
            cv2.imshow("Screen", img_bgr)
            if(cv2.waitKey(1) & 0xFF == ord('q')):
                break

    cv2.destroyAllWindows()
