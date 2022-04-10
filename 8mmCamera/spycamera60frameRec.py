import cv2
import os
import time
import datetime
import RPi.GPIO as GPIO
import sys
import numpy as np

camera              = 0
timingPin           = 2
imgNum              = 0
fileNum             = 1
recFlag             = False
size                = 1     #0:320x240      1:640x480       2:800x600   3:1280x720
setFPS              = 0     #0:16   1:24    2:32    3:48    4:64    5:90
recFPS              = 16
maxSec              = 30
maxFrame            = recFPS * maxSec
timeLog             = []
imgMem              = []
recStopThreshold    = 5.0   #sec

filePath = "/home/pi/Workspace/8mmCamera/"


def rec60Frame():
    print("rec60Frame")
    global setFPS,timeLog,targetFPS
    i = 0
    startTime = time.time()
    targetTime = time.time() + (1/targetFPS)
    while i < 60:
        if time.time() > targetTime:
            timeLog.append(time.time())
            targetTime=timeLog[-1] + (1/targetFPS)
            imgRec()
            i += 1
    movieSave()

def timingPinWasPushed(gpio_pin):
    #global timeLog
    #timeLog.append(time.time())
    #imgRec()
    print("pushed")
    rec60Frame()

GPIO.setmode(GPIO.BCM)
GPIO.setup(timingPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.add_event_detect(timingPin, GPIO.FALLING, callback = timingPinWasPushed, bouncetime = 500)

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
elif size == 3:
    WIDTH  = 1280
    HEIGHT = 720
else:
    WIDTH  = 640
    HEIGHT = 480

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
elif setFPS == 5:
    targetFPS   = 90
else:
    targetFPS   = 16

cycle = 1/targetFPS

#カメラ入力インスタンス定義
capture = cv2.VideoCapture(camera)
codec = cv2.VideoWriter_fourcc(*'mp4v')

if capture.isOpened() is False:
  raise IOError

#解像度変更
capture.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
os.system("v4l2-ctl -d /dev/video0 -p 60")

#==== for raspi spy camera ov564y
os.system('v4l2-ctl -d /dev/video0 -c brightness=50')               #0-100
os.system('v4l2-ctl -d /dev/video0 -c contrast=50')                  #-100-100
os.system('v4l2-ctl -d /dev/video0 -c saturation=0')                #-100-100    
os.system('v4l2-ctl -d /dev/video0 -c red_balance=900')            #1-7999
os.system('v4l2-ctl -d /dev/video0 -c blue_balance=1000')           #1-7999
os.system('v4l2-ctl -d /dev/video0 -c sharpness=0')                 #0-100
os.system('v4l2-ctl -d /dev/video0 -c color_effects=0')             #0:None 1:Mono 2:Sepia 3:Negative 14:Antique 15:set cb/cr
os.system('v4l2-ctl -d /dev/video0 -c rotate=180')                  #0-360
os.system('v4l2-ctl -d /dev/video0 -c video_bitrate_mode=0')        #0:variable 1:Constant
os.system('v4l2-ctl -d /dev/video0 -c video_bitrate=10000000')      #25000-25000000 2500step
os.system('v4l2-ctl -d /dev/video0 -c auto_exposure=1')             #0:auto 1:manual 
os.system('v4l2-ctl -d /dev/video0 -c exposure_time_absolute=5000') #1-10000
os.system('v4l2-ctl -d /dev/video0 -c auto_exposure_bias=12')        #0-24
os.system('v4l2-ctl -d /dev/video0 -c white_balance_auto_preset=0') #0:manual 1:auto 2:Incandescent 3:fluorescent 4:fluorescent m 5:horizon
                                                                    #6:daylight 7:flash 8:cloudy 9:shade 10:grayworld
os.system('v4l2-ctl -d /dev/video0 -c iso_sensitivity_auto=0')      #0:manual 1:auto
os.system('v4l2-ctl -d /dev/video0 -c iso_sensitivity=3')           #0:0 1:100000 2:200000 3:400000 4:800000


#==== for raspi camera v2 imx219
#os.system('v4l2-ctl -d /dev/video0 -c auto_exposure=1')                 #0:Auto mode 1:Manual mode
#os.system('v4l2-ctl -d /dev/video0 -c exposure_time_absolute=1000')     # min=1 max=10000 step=1 default=1000 value=1000
#os.system('v4l2-ctl -d /dev/video0 -c auto_exposure_bias=12')           #0: -4000   ....    12:0    ....    24:4000
#os.system('v4l2-ctl -d /dev/video0 -c white_balance_auto_preset=3')     #0: Manual	1: Auto	2: Incandescent 3: Fluorescent 4: Fluorescent H
#				                                                        #5: Horizon	6: Daylight 7: Flash    8: Cloudy   9: Shade    10: Greyworld
#os.system('v4l2-ctl -d /dev/video0 -c iso_sensitivity_auto=0')          #0: Manual	1: Auto
#os.system('v4l2-ctl -d /dev/video0 -c iso_sensitivity=0')               #0: 0 (0x0)	1: 100000 (0x186a0) 2: 200000 (0x30d40)	3: 400000 (0x61a80)	4: 800000 (0xc3500)



def movieSave():
    global imgNum,timeLog,codec,imgMem
    print(imgNum)
    print(len(timeLog))
    print(len(imgMem))
    resultFPS =1/((timeLog[-1] - timeLog[0])/(len(timeLog)-1))
    today = datetime.datetime.now()
    fileName = filePath + today.strftime("%Y%m%d_%H%M%S") + ".mp4"
    video = cv2.VideoWriter(fileName, codec, recFPS, (WIDTH, HEIGHT))

    if not video.isOpened():
        print("can't be opened")
        sys.exit()

    startTime = time.time()
    for i in range(1,imgNum):
        print(str(i) + "/" + str(imgNum))
        img = imgMem[i]
        video.write(img)
    print(time.time() - startTime)
    video.release()
    print("result FPS = " + str(resultFPS))
    imgNum = 0
    imgMem = []
    timeLog = []

   
def imgRec():
    global capture,imgNum,frame,imgMem

    ret, frame = capture.read()
    if ret is False:
        raise IOError
    imgMem.append(frame)
    imgNum += 1

timeStart = time.time()

if capture.isOpened() is False:
    raise IOError



while(True):

    time.sleep(1.0)  
    #if imgNum > 0:  
    #    if time.time() - timeLog[-1] >= recStopThreshold:
    #        movieSave()

capture.release()
cv2.destroyAllWindows()   
