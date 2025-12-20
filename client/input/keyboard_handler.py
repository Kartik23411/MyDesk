from pynput.keyboard import Listener as KeyboardListener, Key
from common.constants import MSG_KEY_PRESS
from common.protocol import send_message

class KeyboardHandler:

    def __init__(self, socket):
        self.socket = socket
        self.listener = None

    def on_press(self, key):
        print(f"DEBUG: Key pressed: {key}")  # ✅ Add this
    
        try:
            key_char = key.char
        except AttributeError:
            key_char = key.name

        key_bytes = key_char.encode('utf-8')
        
        print(f"DEBUG: Sending key: {key_char}")  # ✅ Add this
        
        try:
            self.send_callback(key_char)
        except Exception as e:
            print(f"DEBUG: Error sending key: {e}")  # ✅ Add this

    def on_release(self, key):
        pass

    def start(self):
        self.listener = KeyboardListener(
            on_press= self.on_press, 
            on_release= self.on_release
        )
        self.listener.start()

    def stop(self):
        if self.listener:
            self.listener.stop()
            self.listener = None
