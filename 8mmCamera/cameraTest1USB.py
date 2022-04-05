import cv2
import os
import time
import RPi.GPIO as GPIO
timingPin = 2
imgNum = 0
recFlag = False
cycle = 0.0625

def timingPinWasPushed(gpio_pin):
    global recFlag
    recFlag = not recFlag

GPIO.setmode(GPIO.BCM)
GPIO.setup(timingPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.add_event_detect(timingPin, GPIO.FALLING, callback = timingPinWasPushed, bouncetime = 100)

#解像度パラメータ
WIDTH  = 1280   #320/640/800/1024/1280/1920
HEIGHT = 720   #240/480/600/ 576/ 720/1080
CLIP_FPS = 16.0

#カメラ入力インスタンス定義
capture = cv2.VideoCapture(0)

#解像度変更
capture.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

   
def imgSave():
    global recFlag,capFlag,capture,timeStart,imgNum

    ret, frame = capture.read()
    capFlag = True
    timeFinish = time.time() - timeStart
    timeStart = time.time()

    if ret is False:
        raise IOError

    if recFlag == True and capFlag == True:
        fileName = "/home/pi/Workspace/RaspberryPi/8mmCamera/" + str(imgNum)+ ".jpg"   
        print(timeFinish)             
        #cv2.imwrite(fileName,frame)
        imgNum += 1
        capFlag = False

timeStart = time.time()

if capture.isOpened() is False:
    raise IOError

while(True):

    targetTime = timeStart + cycle
    if time.time() >= targetTime:
        imgSave()

