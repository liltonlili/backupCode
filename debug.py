import cv2
import numpy as np
img = cv2.imread("roi.jpg")
cv2.imshow("img", img)
cv2.waitKey(0)