from pynput.keyboard import Controller as PynputKeyboardController, Key

class KeyboardController:

    def __init__(self):
        self.keyboard = PynputKeyboardController()

    def type_key(self, key_str):
        if(len(key_str) == 1):
            self.keyboard.type(key_str)
        else:
            try:
                key_attr = getattr(Key, key_str)
                self.keyboard.press(key_attr)
                self.keyboard.release(key_attr)
            except:
                print("Invalid key pressed")