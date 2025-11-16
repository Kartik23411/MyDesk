from mss import mss

def get_screen_size():
    with mss() as sct:
        monitor = sct.monitors[0]
        return (monitor['width'], monitor['height'])