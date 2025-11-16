import mss
import cv2
import numpy as np

from common.constants import JPEG_QUALITY

class ScreenCapture:
    def __init__(self, with_cursor=True, monitor_index=1):
        
        self.with_cursor = with_cursor
        self.monitor_index = monitor_index
        self.sct = None

    def start(self):
        self.sct =  mss.mss(with_cursor = self.with_cursor)

    def capture_frame(self):

        sct_img = self.sct.grab(self.sct.monitors[self.monitor_index])

        img_array = np.frombuffer(sct_img.raw, dtype="uint8")
        img_array = img_array.reshape(sct_img.height, sct_img.width, 4) 
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)

        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
        _, jpeg_data = cv2.imencode('.jpg', img_bgr, encode_param)
        jpeg_bytes = jpeg_data.tobytes()

        return (jpeg_bytes, sct_img.width, sct_img.height)

    def stop(self):
        if self.sct:
            self.sct.close()
            self.sct = None

    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
