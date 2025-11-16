import cv2
import struct
from common.constants import MSG_MOUSE_CLICK, MSG_SCROLL, MSG_MOUSE_MOVE
from common.protocol import send_message

class MouseHandler:

    def __init__(self, socket, get_dimensions_callback):
        self.socket = socket
        self.get_dimensions = get_dimensions_callback

    def callback(self, event, x, y, flags, param):
        dims = self.get_dimensions()
        if not dims:
            return
        
        screen_width, screen_height, display_width, display_height = dims

        server_x = int(x * (screen_width / display_width))
        server_y = int(y * (screen_height / display_height))

        if event == cv2.EVENT_MOUSEMOVE:
            payload = struct.pack("!II", server_x, server_y)
            try: 
                send_message(self.socket, MSG_MOUSE_MOVE, payload)
            except:
                pass
        
        #  struct format: (button number, action: 0 release 1 press, server x, server y)
        elif event == cv2.EVENT_LBUTTONDOWN:
            payload = struct.pack("!BBII", 1, 1, server_x, server_y)
            try:
                send_message(self.socket, MSG_MOUSE_CLICK, payload)
            except:
                pass

        elif event == cv2.EVENT_LBUTTONUP:
            payload = struct.pack("!BBII", 1, 0, server_x, server_y)
            try:
                send_message(self.socket, MSG_MOUSE_CLICK, payload)
            except:
                pass

        elif event == cv2.EVENT_RBUTTONDOWN:
            payload = struct.pack("!BBII", 2, 1, server_x, server_y)
            try:
                send_message(self.socket, MSG_MOUSE_CLICK, payload)
            except:
                pass

        elif event == cv2.EVENT_RBUTTONUP:
            payload = struct.pack("!BBII", 2, 0, server_x, server_y)
            try:
                send_message(self.socket, MSG_MOUSE_CLICK, payload)
            except:
                pass

        elif event == cv2.EVENT_MBUTTONDOWN:
            payload = struct.pack("!BBII", 3, 1, server_x, server_y)
            try:
                send_message(self.socket, MSG_MOUSE_CLICK, payload)
            except:
                pass

        elif event == cv2.EVENT_MBUTTONUP:
            payload = struct.pack("!BBII", 3, 0, server_x, server_y)
            try:
                send_message(self.socket, MSG_MOUSE_CLICK, payload)
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
                send_message(self.socket, MSG_SCROLL, payload)
            except:
                pass
