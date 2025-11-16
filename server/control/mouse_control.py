from pynput.mouse import Controller as PynputMouseController, Button

class MouseController:
    def __init__(self):
        self.mouse = PynputMouseController()

    def move(self, x, y):
        self.mouse.position = (x, y)

    def click(self, x, y, button, action):
        self.mouse.position = (x, y)

        match button:
            case 1: button_obj = Button.left
            case 2: button_obj = Button.right
            case 3: button_obj = Button.middle
            case _: raise IOError("Invalid button")

        if(action == 1):
            self.mouse.press(button_obj)
        else: 
            self.mouse.release(button_obj)

    def scroll(self, x, y, delta):
        self.mouse.position = (x, y)
        self.mouse.scroll(0, delta)