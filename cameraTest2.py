import cv2


def get_camera_propaties():
    params = ['MSEC',
            'POS_FRAMES',
            'POS_AVI_RATIO',
            'FRAME_WIDTH',
            'FRAME_HEIGHT',
            'PROP_FPS',
            'PROP_FOURCC',
            'FRAME_COUNT',
            'FORMAT',
            'MODE',
            'BRIGHTNESS',
            'CONTRAST',
            'SATURATION',
            'HUE',
            'GAIN',
            'EXPOSURE',
            'CONVERT_RGB',
            'WHITE_BALANCE',
            'RECTIFICATION']

    cap = cv2.VideoCapture(0)
    for num in range(19):
        print(params[num], ':', cap.get(num))

capture = cv2.VideoCapture(0)


if capture.isOpened() is False:
    raise IOError

while(True):
    ret, frame = capture.read()
    if ret is False:
        raise IOError
    cv2.imshow('frame',frame)
    key = cv2.waitKey(1)
    
    if key == ord("p"): #p
        get_camera_propaties()

    if key == 27: #ESC
        break

capture.release()
cv2.destroyAllWindows()