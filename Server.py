import socket
import mss
import struct
import time

HOST = "192.168.1.115"  
PORT = 6000  

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serversocket:
    serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serversocket.bind((HOST, PORT))
    serversocket.listen(1)
    print(f"Server is listening to {HOST} on {PORT}")

    conn, addr = serversocket.accept()
    print(f"Client connected on {addr}")

    with mss.mss() as sct:
        while True:
            sct_img = sct.grab(sct.monitors[1])
            print(f"The width, height are {sct_img.width} * {sct_img.height} and size is {sct_img.size}")
            print(f"the length of the screenshot {len(sct_img.raw)}")

            metadata = struct.pack("III", sct_img.width, sct_img.height, len(sct_img.raw))
            try: 
                conn.sendall(metadata)
                conn.sendall(sct_img.raw)
                time.sleep(.03)
            except (BrokenPipeError, ConnectionResetError):
                print("Client Disconnected")
                break