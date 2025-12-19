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

import cv2
import struct


class MouseHandler_Async:
    
    def __init__(self, send_callbacks):

        self.send_callbacks = send_callbacks
        self.screen_width = 0
        self.screen_height = 0
        self.display_width = 0
        self.display_height = 0
        
    def set_dimensions(self, screen_w, screen_h, display_w, display_h):
       
        self.screen_width = screen_w
        self.screen_height = screen_h
        self.display_width = display_w
        self.display_height = display_h

    def callback(self, event, x, y, flags, param):
       
        if self.screen_width == 0 or self.screen_height == 0:
            return
        
        # Scale coordinates
        server_x = int(x * (self.screen_width / self.display_width))
        server_y = int(y * (self.screen_height / self.display_height))

        if event == cv2.EVENT_MOUSEMOVE:
            self.send_callbacks['mouse_move'](server_x, server_y)
        
        elif event == cv2.EVENT_LBUTTONDOWN:
            self.send_callbacks['mouse_click'](1, 1, server_x, server_y)

        elif event == cv2.EVENT_LBUTTONUP:
            self.send_callbacks['mouse_click'](1, 0, server_x, server_y)

        elif event == cv2.EVENT_RBUTTONDOWN:
            self.send_callbacks['mouse_click'](2, 1, server_x, server_y)

        elif event == cv2.EVENT_RBUTTONUP:
            self.send_callbacks['mouse_click'](2, 0, server_x, server_y)

        elif event == cv2.EVENT_MBUTTONDOWN:
            self.send_callbacks['mouse_click'](3, 1, server_x, server_y)

        elif event == cv2.EVENT_MBUTTONUP:
            self.send_callbacks['mouse_click'](3, 0, server_x, server_y)

        elif event == cv2.EVENT_MOUSEWHEEL:
            if flags > 0:
                scroll_delta = 1
            else:
                scroll_delta = -1
            self.send_callbacks['scroll'](server_x, server_y, scroll_delta)