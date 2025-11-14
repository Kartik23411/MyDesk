import socket
import struct
import cv2
import numpy as np
from mss import mss
from pynput.keyboard import Listener as KeyboardListener, Key

HOST = "192.168.1.115"  # The server's hostname or IP address
PORT = 6000  # The port used by the server

# Message Constants
MSG_SCREENSHOT = 0x01
MSG_MOUSE_MOVE = 0x02
MSG_MOUSE_CLICK = 0x03
MSG_KEY_PRESS = 0x04
MSG_SCROLL = 0x05

client_socket=None

screen_width=0
screen_height=0

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

def mouse_callback(event, x, y, flags, param):
    global screen_width, screen_height

    if screen_height>0 and screen_width>0:
        display_width, display_height = getscreen_size()

        # scalling according to the display size
        server_x = int(x * (screen_width / display_width))
        server_y = int(y * (screen_height / display_height))

        if event == cv2.EVENT_MOUSEMOVE:
            payload = struct.pack("!II", server_x, server_y)
            try: 
                send_message(param, MSG_MOUSE_MOVE, payload)
            except:
                pass
        
        #  struct format: (button number, action: 0 release 1 press, server x, server y)
        elif event == cv2.EVENT_LBUTTONDOWN:
            payload = struct.pack("!BBII", 1, 1, server_x, server_y)
            try:
                send_message(param, MSG_MOUSE_CLICK, payload)
            except:
                pass

        elif event == cv2.EVENT_LBUTTONUP:
            payload = struct.pack("!BBII", 1, 0, server_x, server_y)
            try:
                send_message(param, MSG_MOUSE_CLICK, payload)
            except:
                pass

        elif event == cv2.EVENT_RBUTTONDOWN:
            payload = struct.pack("!BBII", 2, 1, server_x, server_y)
            try:
                send_message(param, MSG_MOUSE_CLICK, payload)
            except:
                pass

        elif event == cv2.EVENT_RBUTTONUP:
            payload = struct.pack("!BBII", 2, 0, server_x, server_y)
            try:
                send_message(param, MSG_MOUSE_CLICK, payload)
            except:
                pass

        elif event == cv2.EVENT_MBUTTONDOWN:
            payload = struct.pack("!BBII", 3, 1, server_x, server_y)
            try:
                send_message(param, MSG_MOUSE_CLICK, payload)
            except:
                pass

        elif event == cv2.EVENT_MBUTTONUP:
            payload = struct.pack("!BBII", 3, 0, server_x, server_y)
            try:
                send_message(param, MSG_MOUSE_CLICK, payload)
            except:
                pass

        elif event == cv2.EVENT_MOUSEWHEEL:
            if flags>0:
                scroll_delta = 1
            else:
                scroll_delta = -1
            print(f"Scroll detected! Delta: {scroll_delta}") 
            payload = struct.pack('!IIi', server_x, server_y, scroll_delta)
            try:
                send_message(param, MSG_SCROLL, payload)
            except:
                pass

        
def getscreen_size():
    with mss() as sct:
        monitors_info = sct.monitors

        total_width = monitors_info[0]['width']
        total_height = monitors_info[0]['height']
        return (total_width, total_height)

def on_key_press(key):
    global client_socket
    try:
        key_char = key.char
    except AttributeError:
        key_char = key.name

    key_bytes = key_char.encode('utf-8')
    payload = key_bytes

    try:
        send_message(client_socket ,MSG_KEY_PRESS, payload)
    except:
        pass

def on_key_release(key):
    pass

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientsocket:
    clientsocket.connect((HOST, PORT))
    print("Connected to the sever")

    client_socket=clientsocket

    display_width, display_height = getscreen_size() # getting the display size

    keyboard_listener = KeyboardListener(on_press=on_key_press, on_release=on_key_release)
    keyboard_listener.start()

    cv2.namedWindow("Screen") # Creating the window and setting mouse callback function
    cv2.setMouseCallback("Screen", mouse_callback, clientsocket)
    
    while True: 
        msg_type, payload = recv_message(clientsocket)
        
        if(msg_type==MSG_SCREENSHOT):
            metadata = payload[:12]
            width, height, data_size = struct.unpack("III", metadata)
            raw_data = payload[12:]

            screen_width=width
            screen_height=height
            
            jpeg_array = np.frombuffer(raw_data, dtype=np.uint8)
            img_bgr = cv2.imdecode(jpeg_array, cv2.IMREAD_COLOR)
            
            img_bgr = cv2.resize(img_bgr, (display_width, display_height))

            cv2.imshow("Screen", img_bgr)
            if(cv2.waitKey(1) & 0xFF == ord('q')):
                break

    cv2.destroyAllWindows()
