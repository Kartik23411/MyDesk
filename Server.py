import socket
import mss
import struct
import time

HOST = "127.0.0.1"  # ip address of the server
PORT = 6000  

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serversocket: 
    serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serversocket.bind((HOST, PORT))
    serversocket.listen(1)
    print(f"Server is listening to {HOST} on {PORT}")

    while True:
        try:
            conn, addr = serversocket.accept()
            print(f"Client connected on {addr}")

            with mss.mss(with_cursor=True) as sct:
                while True:
                    sct_img = sct.grab(sct.monitors[1])
                    # print(f"The width, height are {sct_img.width} * {sct_img.height} and size is {sct_img.size}")
                    # print(f"the length of the screenshot {len(sct_img.raw)}")

                    # packing the width, height and data length integers in a struct so that data of only valid length is accepted
                    metadata = struct.pack("III", sct_img.width, sct_img.height, len(sct_img.raw))
                    try: 
                        conn.sendall(metadata)
                        conn.sendall(sct_img.raw)
                        time.sleep(.03)
                    except (BrokenPipeError, ConnectionResetError):
                        print("[[Client Disconnected]] Waiting for other ....")
                        break
        except (BrokenPipeError, ConnectionResetError):
            print("Client Disconnected")
        except KeyboardInterrupt:
            print("Shutting down the server...")
            break