import socket
import struct
import cv2
import numpy as np

from common.constants import MSG_SCREENSHOT, DEFAULT_HOST, DEFAULT_PORT
from common.protocol import recv_message
from client.input.keyboard_handler import KeyboardHandler
from client.input.mouse_handler import MouseHandler
from client.utils.display import get_screen_size

screen_width = 0
screen_height = 0
display_width = 0
display_height = 0 

def get_dimensions():
    if screen_width > 0 and screen_height > 0:
        return (screen_width, screen_height, display_width, display_height)
    return None

def main():
    global screen_width, screen_height, display_width, display_height 
    HOST = DEFAULT_HOST
    PORT = DEFAULT_PORT

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientsocket:
        clientsocket.connect((HOST, PORT))
        print("Connected to the server")

        display_width, display_height = get_screen_size()

        keyboard_handler =  KeyboardHandler(clientsocket)
        keyboard_handler.start()

        mouse_handler = MouseHandler(clientsocket, get_dimensions)

        cv2.namedWindow("MyDesk - Access Anytime")
        cv2.setMouseCallback("MyDesk - Access Anytime", mouse_handler.callback, None)

        try:
            while True: 
                msg_type, payload = recv_message(clientsocket)
        
                if(msg_type==MSG_SCREENSHOT):
                    metadata = payload[:12]
                    width, height, data_size = struct.unpack("III", metadata)
                    raw_data = payload[12:]

                    screen_width = width
                    screen_height = height
                    
                    jpeg_array = np.frombuffer(raw_data, dtype=np.uint8)
                    img_bgr = cv2.imdecode(jpeg_array, cv2.IMREAD_COLOR)
                    
                    img_bgr = cv2.resize(img_bgr, (display_width, display_height))

                    cv2.imshow("MyDesk - Access Anytime", img_bgr)
                    if(cv2.waitKey(1) & 0xFF == ord('q')):
                        break
        except KeyboardInterrupt:
            print("Client Disconnected")
        finally:
            keyboard_handler.stop()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
