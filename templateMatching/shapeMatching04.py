import cv2
import numpy as np
from PIL import Image as im

WIDTH  = 1280  #320/640/800/1024/1280/1920
HEIGHT = 720  #240/480/600/ 576/ 720/1080

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

def makeTemplateContours():
    template = cv2.imread("Template.jpg")
    edgeTemp = cv2.Canny(template,threshold1=300,threshold2=1000)
    tempContours, hierarchy = cv2.findContours(edgeTemp,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    cimg = np.zeros((template.shape[0],template.shape[1],3))
    cimg = cv2.drawContours(cimg, tempContours, 1, (255,255,255), 1)
#    cv2.imshow('temp',cimg)
    tempCont = tempContours[1]
    return(tempCont,cimg)

def contours(edge):

    contours, hierarchy = cv2.findContours(edge,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    cimg = np.zeros((edge.shape[0],edge.shape[1],3))

    try:
        cimg = cv2.drawContours(cimg, contours, 1, (255,255,255), 1)
        cnt = contours[1]
        return(cimg,cnt)
    except:
        print("no contours.")
        return(cimg,False)


if capture.isOpened() is False:
    raise IOError

tempCnt,tempCimg = makeTemplateContours()

while True:
    ret, frame = capture.read()
    
    if ret is False:
        raise IOError

#    frame = frame[300:710, 680:1390, :]
    gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
#    gray = cv2.medianBlur(gray,ksize)
    th, binary = cv2.threshold(gray, binth, maxValue, cv2.THRESH_TOZERO)
    edge = cv2.Canny(binary,threshold1=th1,threshold2=th2)

    edge2 = edge.copy()
    cimg,cnt = contours(edge2)

    if cnt is not False:
        match = cv2.matchShapes(tempCnt, cnt, cv2.CONTOURS_MATCH_I3, 0)
        if match < 0.03:
            result = "OK"
            color = (255,0,0)

        else:
            result = "NG"
            color = (0,0,255)
    else:
        match = 0
        result = "--"
        color = (255,255,255)



    cv2.putText(tempCimg,"Template",(30,90),cv2.FONT_HERSHEY_SIMPLEX,3.0,255,2,cv2.LINE_AA)
    cv2.putText(cimg,result + " / differ = " + "{:.4f}".format(match),(30,90),cv2.FONT_HERSHEY_SIMPLEX,3.0,color,2,cv2.LINE_AA)
    

    concat1 = cv2.vconcat([gray,binary])
    concat1 = cv2.cvtColor(concat1,cv2.COLOR_GRAY2RGB)

    cv2.putText(concat1,"image",(30,90),cv2.FONT_HERSHEY_SIMPLEX,3.0,(0,255,0),2,cv2.LINE_AA)
   
    concat2 = cv2.vconcat([tempCimg,cimg])
    concat2 = concat2.astype('uint8')
    concat3 = cv2.hconcat([concat1,concat2])
    concat3 = cv2.resize(concat3 , (int(concat3.shape[1]*0.5), int(concat3.shape[0]*0.5)))
    cv2.imshow('result',concat3)
#    cv2.imshow('frame',edge)

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

        cv2.imwrite("Template.jpg",binary)
        tempCnt,tempCimg = makeTemplateContours()

capture.release()
cv2.destroyAllWindows()