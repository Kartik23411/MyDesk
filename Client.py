import socket
import struct
import cv2
import numpy as np

HOST = "localhost"  # The server's hostname or IP address
PORT = 6000  # The port used by the server

def recv_exact(sock, n):
    data = b''
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Connection Closed")
        data += chunk
    return data

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientsocket:
    clientsocket.connect((HOST, PORT))
    print("Connected to the sever")
    
    while True: 
        metadata = recv_exact(clientsocket, 12)
        width, height, data_size = struct.unpack("III", metadata)
        raw_data = recv_exact(clientsocket, data_size)
        img_array = np.frombuffer(raw_data, dtype=np.uint8)
        img_array = img_array.reshape(height, width, 4)
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)
        cv2.imshow("Screen", img_bgr)
        if(cv2.waitKey(1) & 0xFF == ord('q')):
            break

    cv2.destroyAllWindows()
