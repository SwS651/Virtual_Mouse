import cv2
import numpy as np
import HandTrackingModule as htm
import time
import win32api
# from pynput.mouse import Controller as MouseController
from pynput.mouse import Button, Controller as MouseController

# 320, 240
WIDTH_CAM, HEIGHT_CAM = 320, 240


CHANGES_MODE = ["double", "right", "scroll"]

# Get screen dimensions
# wScr, hScr = win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)


class VirtualMouseController:
    def __init__(self):
        self.mouse = MouseController()
        self.plocX, self.plocY, self.clocX, self.clocY = 0,0,0,0
        self.time_last_clicked, self.latest_time = time.time(), time.time()
        self.time_last_detected = 0
        self.gesture_mode = False
        self.selected_mode = 0
        self.scrolling = None

        self.detector = htm.handDetector(maxHands=1)

    def get_mouse_status(self):
        return self.gesture_mode
    def get_selected_mode(self):
        return str(CHANGES_MODE[self.selected_mode])
    
    def move_mouse(self, x, y):
        SMOOTHENING = 5
        self.clocX = self.plocX + (x - self.plocX) / SMOOTHENING
        self.clocY = self.plocY + (y - self.plocY) / SMOOTHENING

        self.mouse.position = (win32api.GetSystemMetrics(0) - self.clocX, self.clocY)
        self.plocX, self.plocY = self.clocX, self.clocY

    def left_click(self,length):
        # Click mouse if distance short
        if length < 25 and time.time() - self.time_last_clicked > 0.5:
            self.mouse.click(Button.left)
            self.time_last_clicked = time.time()
    
    def double_click(self):
        if time.time() - self.time_last_clicked  > 1.0:
            self.mouse.click(Button.left, 2)
            self.time_last_clicked  = time.time()

    def right_click(self):
        if time.time() - self.time_last_clicked  > 1.5:
            self.mouse.click(Button.right, 1)
            self.time_last_clicked  = time.time()

    def scrolling_mouse(self):
        if time.time() - self.time_last_clicked  > 0.2:
            if self.plocY - self.scrolling > 8:
                self.mouse.scroll(0, 1)
            elif self.plocY - self.scrolling < -8:
                self.mouse.scroll(0, -1)

            self.time_last_clicked  = time.time()

    def tracking(self,img):
        FRAME_R = 100
        # Process every Nth frame to reduce processing load
        # if frame_count % 2 == 0:
        img = self.detector.findHands(img)
        lmList, bbox = self.detector.findPosition(img)

        #  Get the tip of the index and middle fingers
        if len(lmList) != 0:
            index_fingerX, index_fingerY = lmList[8][1:]

            # 3. Check which fingers are up
            fingers = self.detector.fingersUp()
            cv2.rectangle(img, (FRAME_R, FRAME_R), (WIDTH_CAM - FRAME_R, HEIGHT_CAM - FRAME_R), (255, 0, 255),2)

            # 4. Only Index Finger : Moving Mode
            if fingers[1] == 1 and fingers[2] == 0:
                self.latest_time = time.time()

                if self.gesture_mode == False and self.time_last_detected == 0:
                    self.time_last_detected = time.time()

                if self.latest_time - self.time_last_detected >= 1.8:
                    self.gesture_mode = True

            if self.gesture_mode:
                # Convert the coordinates
                x3 = np.interp(index_fingerX, (FRAME_R, WIDTH_CAM - FRAME_R), (0, win32api.GetSystemMetrics(0)))
                y3 = np.interp(index_fingerY, (FRAME_R, HEIGHT_CAM - FRAME_R), (0, win32api.GetSystemMetrics(1)))

                # Mouse Moving
                self.move_mouse(x3, y3)
                cv2.circle(img, (index_fingerX, index_fingerY), 15, (255, 0, 255), cv2.FILLED)

                # Left click
                if fingers[1] == 1 and fingers[2] == 1 and fingers[0] == 0:

                    # Step9: Find distance between fingers
                    length, _, lineInfo = self.detector.findDistance(8, 12, img)
                    # Click mouse if distance short
                    self.left_click(length)
                    cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 255, 0), cv2.FILLED)


                # Double clicks
                if fingers[1] == 1 and fingers[4] == 1 and fingers[3] == 0 and CHANGES_MODE[self.selected_mode] == "double":
                    length, _, lineInfo = self.detector.findDistance(8, 20, img)
                    self.double_click()
                    cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 0, 255), cv2.FILLED)
                        

                # Right clicks
                if fingers[1] == 1 and fingers[3] == 0 and fingers[4] == 1 and CHANGES_MODE[self.selected_mode] == "right":
                    length, _, lineInfo = self.detector.findDistance(8, 20, img)
                    self.right_click()
                    cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 0, 255), cv2.FILLED)
 

            # Scroll action
            if fingers[1] == 1 and fingers[3] == 0 and fingers[4] == 1 and CHANGES_MODE[self.selected_mode] == "scroll":
                if self.scrolling == None:
                    self.scrolling = self.plocY
                self.scrolling_mouse()
    
            else:
                self.scrolling = None

            # Use thumb to change gesture mode
            if fingers[0] == 1 and fingers[1] == 0:
                if time.time() - self.time_last_clicked > 1:
                    if self.selected_mode != len(CHANGES_MODE) - 1:
                        self.selected_mode += 1
                    else:
                        self.selected_mode = 0
                    self.time_last_clicked = time.time()
                    print(CHANGES_MODE[self.selected_mode])

            if time.time() - self.latest_time >= 3:
                # cv2.putText(img, "Mode: Disabled", (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
                self.gesture_mode = False
                self.time_last_detected = 0
            # else:
                # cv2.putText(img, "Mode: Enabled", (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
            


def main():
    cap = cv2.VideoCapture(0)
    cap.set(3, WIDTH_CAM)
    cap.set(4, HEIGHT_CAM)

    hand_tracking_controller = VirtualMouseController()
    frame_count = 0
    while True:
        _, img = cap.read()
        hand_tracking_controller.tracking(img,frame_count)
        frame_count += 1

        # Display
        # self.img = cv2.flip(self.img, 1)
        # cv2.imshow("image", img)
        cv2.waitKey(1)

if __name__ == "__main__":
    main()

