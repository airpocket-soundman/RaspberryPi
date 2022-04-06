import cv2
import os
import time
import datetime
import RPi.GPIO as GPIO
import sys

camera      = 0
size        = 3     #0:320x240      1:640x480       2:800x600
setFPS      = 3     #0:16   1:24    2:32    3:48    4:64
timingPin   = 2
imgNum      = 0
recFlag     = False
recFlagOld  = False

filePath = "/home/pi/Workspace/RaspberryPi/8mmCamera/"

def timingPinWasPushed(gpio_pin):
    global recFlag,imgNum,timeLog
    if recFlag == False:
        recFlag = True
        print("start recording")
    else:
        recFlag = False
        print("finish recording")

GPIO.setmode(GPIO.BCM)
GPIO.setup(timingPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.add_event_detect(timingPin, GPIO.FALLING, callback = timingPinWasPushed, bouncetime = 100)

#解像度パラメータ
if size == 0:
    WIDTH  = 320   #320/640/800/1024/1280/1920
    HEIGHT = 240   #240/480/600/ 576/ 720/1080
elif size == 1:
    WIDTH  = 640
    HEIGHT = 480
elif size == 2:
    WIDTH  = 800
    HEIGHT = 600
else:
    WIDTH  = 160
    HEIGHT = 120

if   setFPS == 0:
    targetFPS   = 16
elif setFPS == 1:
    targetFPS   = 24
elif setFPS == 2:
    targetFPS   = 32
elif setFPS == 3:
    targetFPS   = 48
elif setFPS == 4:
    targetFPS   = 64
else:
    targetFPS   = 16


cycle = 1/targetFPS - 0.0

os.system('v4l2-ctl -d /dev/video0 -c auto_exposure=1')                 #0:Auto mode 1:Manual mode
os.system('v4l2-ctl -d /dev/video0 -c exposure_time_absolute=1000')     # min=1 max=10000 step=1 default=1000 value=1000
os.system('v4l2-ctl -d /dev/video0 -c auto_exposure_bias=12')           #0: -4000   ....    12:0    ....    24:4000
os.system('v4l2-ctl -d /dev/video0 -c white_balance_auto_preset=3')     #0: Manual	1: Auto	2: Incandescent 3: Fluorescent 4: Fluorescent H
				                                                        #5: Horizon	6: Daylight 7: Flash    8: Cloudy   9: Shade    10: Greyworld
os.system('v4l2-ctl -d /dev/video0 -c iso_sensitivity_auto=0')          #0: Manual	1: Auto
os.system('v4l2-ctl -d /dev/video0 -c iso_sensitivity=0')               #0: 0 (0x0)	1: 100000 (0x186a0) 2: 200000 (0x30d40)	3: 400000 (0x61a80)	4: 800000 (0xc3500)

#カメラ入力インスタンス定義
capture = cv2.VideoCapture(camera)
codec = cv2.VideoWriter_fourcc(*'mp4v')


if capture.isOpened() is False:
  raise IOError

#解像度変更
capture.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

def movieSave():
    global imgNum,timeLog,codec,recFlag,capture,timeStart,targetFPS
    imgNum = 0
    today = datetime.datetime.now()
    fileName = filePath + today.strftime("%Y%m%d_%H%M%S") + ".mp4"
    video = cv2.VideoWriter(fileName, codec, targetFPS, (WIDTH, HEIGHT))

    if not video.isOpened():
        print("can't be opened")
        sys.exit()

    while recFlag == True:
        targetTime = timeStart + cycle
        if time.time() >= targetTime:
            timeLog = timeStart
            timeStart = time.time()
            ret, frame = capture.read()
            #print(timeStart - timeLog)
            video.write(frame)
            #print(imgNum)
            if imgNum == 0:
                timeLogStart = timeStart
            imgNum += 1
        #time.sleep(0.01)
    timeLogEnd = timeStart
    try:
        resultFPS = 1/((timeLogEnd - timeLogStart)/imgNum)
    except:
        resultFPS = 0

    video.release()
    print("result FPS = " + str(resultFPS))
    print("frame num  = " + str(imgNum + 1))
    imgNum = 0

timeStart = time.time()

if capture.isOpened() is False:
    raise IOError

while(True):
    if recFlag != recFlagOld:
        recFlagOld = recFlag
        if recFlag == True:
            movieSave()

    time.sleep(0.1)


capture.release()
cv2.destroyAllWindows()   