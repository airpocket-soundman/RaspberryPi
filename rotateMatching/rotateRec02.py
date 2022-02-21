import cv2
import numpy as np
import math
from PIL import Image as im

WIDTH  = 1920  #320/640/800/1024/1280/1920
HEIGHT = 1080  #240/480/600/ 576/ 720/1080

th1 = 300
th2 = 1000
picNum = 0
ksize = 3
binth = 250
maxValue = 255

capture = cv2.VideoCapture(0)
capture.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
capture.set(cv2.CAP_PROP_EXPOSURE,-100.0)

def contours(img,edge):

    contours, hierarchy = cv2.findContours(edge,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    cimg = np.zeros((edge.shape[0],edge.shape[1],3))
    try:
        cimg = cv2.drawContours(cimg, contours, 0, (255,255,255), 3)
        cnt = contours[0]
        M = cv2.moments(cnt)

        cx = int(M['m10']/M['m00'])
        cy = int(M['m01']/M['m00'])
        center = (cx,cy)
        scale = 1.0
        
        area = cv2.contourArea(cnt)
        perimeter = cv2.arcLength(cnt,True)
        
        rect = cv2.minAreaRect(cnt)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
#        edge = cv2.drawContours(edge,[box],0,255,2)
        
        rows,cols = cimg.shape[:2]
        [vx,vy,x,y] = cv2.fitLine(cnt, cv2.DIST_L2,0,0.01,0.01)
        lefty = int((-x*vy/vx) + y)
        righty = int(((cols-x)*vy/vx)+y)
#        edge = cv2.line(cimg,(cols-1,righty),(0,lefty),(255,255,255),2)
        angle = math.degrees(math.atan2((righty-lefty), (cols-1-0)))
        
        trans = cv2.getRotationMatrix2D(center, angle , scale)
        img2 = cv2.warpAffine(img, trans, (img.shape[1],img.shape[0]))
        cv2.imshow('rec',img2)
        print(box)
        print("area = ", area)
        print("perimeter = ", perimeter)
        print(arg)
        
        
        
    except:
        print("no contours.")

    
    cv2.imshow('cimg',cimg)
#    cv2.imshow('rec',img2)
    
#    return(cimg)

if capture.isOpened() is False:
    raise IOError


while True:
    ret, frame = capture.read()
    
    if ret is False:
        raise IOError

    frame = frame[300:710, 680:1390, :]
    gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray,ksize)
    th, binary = cv2.threshold(gray, binth, maxValue, cv2.THRESH_TOZERO)
    edge = cv2.Canny(binary,threshold1=th1,threshold2=th2)
    
    frame2 = frame.copy()
    edge2 = edge.copy()
    gray2 = gray.copy()
    cimg = contours(gray2,edge2)
#    matching(cimg)
    
    concat = cv2.vconcat([gray,edge])
    

    cv2.imshow('concat',concat)
#    cv2.imshow('frame',frame)
#    cv2.imshow('edge',edge)

    key = cv2.waitKey(1)
    if key == 27: #ESC
        break
    elif key == ord("u"): #p
        th1 += 10
        print("th1 = ",th1)
    elif key == ord("j"):
        th1 -= 10
        print("th1 = ",th1)
    elif key == ord("i"):
        th2 += 10
        print("th2 = ",th2)
    elif key == ord("k"):
        th2 -= 10
        print("th2 = ",th2)
    elif key == ord("o"):
        binth += 10
        print("bth = ",binth)
    elif key == ord("l"):
        binth -= 10
        print("bth = ",binth)
    elif key == ord("y"):
        ksize += 2
        print("ksize = ",ksize)
    elif key == ord("h"):
        ksize -= 2
        if ksize <= 1:
            ksize = 1
        print("ksize = ",ksize)
    elif key == ord("p"):
        cv2.imwrite("edge" + str(picNum) + ".jpg",edge)
        cv2.imwrite("gray" + str(picNum) + ".jpg",gray)
        cv2.imwrite("binary" + str(picNum) + ".jpg",binary)
        cv2.imwrite("cimg" + str(picNum) + ".jpg",cimg)
capture.release()
cv2.destroyAllWindows()