import cv2
import os
import time
import datetime
import RPi.GPIO as GPIO
import sys
camera      = 0
timingPin   = 2
imgNum      = 0
fileNum     = 1
recFlag     = False
targetFPS = 16
timeLog = []
cycle = 1/targetFPS - 0.002
filePath = "/home/pi/Workspace/RaspberryPi/8mmCamera/"

def timingPinWasPushed(gpio_pin):
    global recFlag,imgNum,timeLog
    recFlag = not recFlag
    if recFlag == False:
        movieSave()
    else:
        print("rec start")

GPIO.setmode(GPIO.BCM)
GPIO.setup(timingPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.add_event_detect(timingPin, GPIO.FALLING, callback = timingPinWasPushed, bouncetime = 100)

#解像度パラメータ
WIDTH  = 640   #320/640/800/1024/1280/1920
HEIGHT = 480   #240/480/600/ 576/ 720/1080

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
    global imgNum,timeLog,codec
    print(imgNum)
    print(len(timeLog))
    resultFPS =1/((timeLog[-1] - timeLog[0])/(len(timeLog)-1))
    print(resultFPS)
    today = datetime.datetime.now()
    fileName = filePath + today.strftime("%Y%m%d_%H%M%S") + ".mp4"
    video = cv2.VideoWriter(fileName, codec, resultFPS, (WIDTH, HEIGHT))

    if not video.isOpened():
        print("can't be opened")
        sys.exit()

    for i in range(0,imgNum):
        fileName = filePath + str(i)+ ".jpg"
        img = cv2.imread(fileName)
        video.write(img)
        print(str(i) + "/" + str(imgNum))

    video.release()
    print("result FPS = " + str(resultFPS))
    imgNum = 0
    timeLog = []

   
def imgSave():
    global recFlag,capFlag,capture,timeStart,imgNum,frame

    ret, frame = capture.read()
    capFlag = True
    #timeFinish = time.time() - timeStart
    timeStart = time.time()

    if ret is False:
        raise IOError

    if recFlag == True and capFlag == True:
        fileName = filePath + str(imgNum)+ ".jpg"   
        #print(timeFinish)
        cv2.imwrite(fileName,frame)
        #cv2.imshow("frame",frame)
        imgNum += 1
        timeLog.append(timeStart)
        capFlag = False

timeStart = time.time()

if capture.isOpened() is False:
    raise IOError

while(True):

    targetTime = timeStart + cycle
    if time.time() >= targetTime:
        imgSave()
        
    
    #key = cv2.waitKey(1)
    #if key == 27: #ESC
    #    break

capture.release()
cv2.destroyAllWindows()   