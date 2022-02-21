import cv2

WIDTH  = 1920  #320/640/800/1024/1280/1920
HEIGHT = 1080  #240/480/600/ 576/ 720/1080

capture = cv2.VideoCapture(0)
capture.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
capture.set(cv2.CAP_PROP_EXPOSURE,25.0)

if capture.isOpened() is False:
    raise IOError

ret, frame = capture.read()
if ret is False:
    raise IOError
frame = frame[300:710, 680:1390, :]
cv2.imshow('frame',frame)
key = cv2.waitKey(0)
#if key == 27: #ESC
#    break

capture.release()
cv2.destroyAllWindows()