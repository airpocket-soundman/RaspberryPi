import cv2

#WIDTH  = 1280  #320/640/800/1024/1280/1920
#HEIGHT = 720   #240/480/600/ 576/ 720/1080

capture = cv2.VideoCapture(0)
#capture.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
#capture.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
#capture.set(cv2.CAP_PROP_EXPOSURE, 2000.0)


if capture.isOpened() is False:
    raise IOError

while(True):
    ret, frame = capture.read()
    if ret is False:
        raise IOError
    cv2.imshow('frame',frame)
    key = cv2.waitKey(1)
    if key == 27: #ESC
        break

capture.release()
cv2.destroyAllWindows()