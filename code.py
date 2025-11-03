# from mss import mss

# with mss() as sct:
#     for _ in range(100):
#         sct.shot()

import time

import cv2
import numpy as np
from PIL import ImageGrab

import mss


def screen_record() -> int:
    # 800x600 windowed mode
    mon = (0, 0, 1920, 1080)

    title = "[PIL.ImageGrab] FPS benchmark"
    fps = 0
    last_time = time.time()

    # while time.time() - last_time < 1:
    while True:   
        img = np.asarray(ImageGrab.grab(bbox=mon))
        fps += 1

        cv2.imshow(title, cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        if cv2.waitKey(45) & 0xFF == ord("q"):
            cv2.destroyAllWindows()
            break

    return fps


def screen_record_efficient() -> int:
    # 800x600 windowed mode
    mon = {"top": 0, "left": 0, "width": 1920, "height": 1080}

    title = "[MSS] FPS benchmark"
    fps = 0
    sct = mss.mss()
    last_time = time.time()

    while time.time() - last_time < 1:
        img = np.asarray(sct.grab(mon))
        fps += 1

        cv2.imshow(title, img)
        if cv2.waitKey(45) & 0xFF == ord("q"):
            cv2.destroyAllWindows()
            break

    return fps


print("PIL:", screen_record())
# print("MSS:", screen_record_efficient())