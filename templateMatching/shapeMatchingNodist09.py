# ワークの輪郭を抽出して、テンプレートとの類似度を計算。しきい値以上の類似度の場合はNGとする
# ワークの凹み形状を数値化し、規定の凹み形状よりも多くの凹みが検出された場合は、NGと判断する
# 
#
# t/g　     類似度合否判定のしきい値
# y/h       median blurのしきい値
# u/j       th1
# i/k       th2
# o/l       binTh
# p         テンプレート更新
# ESC       プログラム終了


import cv2
import numpy as np
from PIL import Image as im
import time
import os

#カメラの露出、ホワイトバランスを固定
os.system('v4l2-ctl -d /dev/video0 -c exposure_auto=1 -c exposure_absolute=300')
os.system('v4l2-ctl -d /dev/video0 -c white_balance_temperature_auto=0')
os.system('v4l2-ctl -d /dev/video0 -c white_balance_temperature=4600')

#カメラ解像度指定。カメラによって使える解像度は異なる。
WIDTH  = 1280  #320/640/800/1024/1280/1920
HEIGHT = 720   #240/480/600/ 576/ 720/1080

#camera歪みキャリブレーション USBカメラ、1280×720サイズで調整
#カメラ解像度、カメラ変更の場合はcameratestUndist01.pyで係数測定が必要
#https://qiita.com/ReoNagai/items/5da95dea149c66ddbbdd

mtx  = np.array([[4.88537936e+03,0.0,6.24772642e+02],[0.0,4.84481440e+03,3.54634299e+02],[0.0,0.0,1.0]])
dist = np.array([9.40016759e+00,-7.86181791e+02,3.50155397e-02,-6.47058512e-02,2.08359575e+04])

alpha = 1
newKK, roiSize = cv2.getOptimalNewCameraMatrix(mtx, dist, (WIDTH,HEIGHT), alpha, (WIDTH,HEIGHT))
mapX, mapY = cv2.initUndistortRectifyMap(mtx, dist, None, newKK, (WIDTH,HEIGHT), cv2.CV_32FC1)

#しきい値設定
th1 = 300               #cannyフィルタ用しきい値
th2 = 1000              #cannyフィルタ用しきい値
ksize = 1               #median blur用しきい値 -1でフィルタ不使用
binTh = 100             #binary処理用しきい値
maxValue = 255          #binary処理用しきい値
differTh = 0.10         #類似度判定のしきい値
dentNum = 4             #OK品の凹形状数
nomalDepthTh = 16000    #OK品の凹深さしきい値
ngDepthTh = 500         #NG品の凹深さしきい値
waitCycle = 3           #カメラ安定までの待ちサイクル数
counter = waitCycle + 1 #待ちサイクル値の初期化

#描画設定
drawCnt = True
drawDent = True

#カメラ設定
capture = cv2.VideoCapture(0)
capture.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
#capture.set(cv2.CAP_PROP_EXPOSURE,-100.0)

if capture.isOpened() is False:
    raise IOError

def makeTemplateContours():     #OK品テンプレートの輪郭データ作成

    #テンプレート画像読み込み、サイズ変更
    template = cv2.imread("./Template.jpg")
    template = cv2.resize(template, (WIDTH, HEIGHT))
    #テンプレート画像の輪郭抽出（Cannyフィルタ）
    edgeTemp = cv2.Canny(template,threshold1=th1,threshold2=th2)
    #輪郭線データを取得
    contours, hierarchy = cv2.findContours(edgeTemp,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

    maxRect = 0
    cntNum = 0
    for i in range(len(contours)):
        x,y,w,h = cv2.boundingRect(contours[i])
        if (w * h) > maxRect:
            maxRect = w * h
            cntNum = i
    
    #黒背景作成
    cimg = np.zeros((edgeTemp.shape[0],edgeTemp.shape[1],3))

    try:        #輪郭データを得られた場合は、輪郭画像を描画、輪郭データと輪郭画像を返す
        cimg = cv2.drawContours(cimg, contours, cntNum, (255,255,255), 1)
        return(contours[cntNum],cimg)
    except:     #輪郭データを得られなかった場合
        print("no contours.")
        return(False, cimg)

def preprocess(frame):  #画像の前処理。

    #カメラ画像の歪補正処理
    undistFrame = cv2.remap(frame, mapX, mapY, cv2.INTER_LINEAR)
    
    #カメラ画像をグレースケールに変換
    gray = cv2.cvtColor(undistFrame,cv2.COLOR_BGR2GRAY)

    #medidan blurでノイズ除去
    if ksize >= 1:
        gray = cv2.medianBlur(gray,ksize)
    
    #画像を二値化
    th, binary = cv2.threshold(gray, binTh, maxValue, cv2.THRESH_BINARY)

    edge = cv2.Canny(binary,threshold1=th1,threshold2=th2)

    return(undistFrame,gray,binary,edge)

def contours(frame,edge):             #輪郭データ作成

    #輪郭線データを取得
    contours, hierarchy = cv2.findContours(edge,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    
    #輪郭線データのうち、もっとも大きな外接矩形を持つものを選択    
    maxRect = 0
    cntNum = 0
    for i in range(len(contours)):
        x,y,w,h = cv2.boundingRect(contours[i])
        if (w * h) > maxRect:
            maxRect = w * h
            cntNum = i
    
    #黒背景作成
    cimg = np.zeros((edge.shape[0],edge.shape[1],3))

    try:        #輪郭データを得られた場合は、輪郭画像を描画、輪郭データと輪郭画像を返す

        cimg = cv2.drawContours(cimg, contours, cntNum, (255,255,255), 1)
        if drawCnt is True:
            frame = cv2.drawContours(frame, contours, cntNum, (0,255,0), 3)
        return(contours[cntNum],frame,cimg)
    except:     #輪郭データを得られなかった場合
        print("no contours.")
        return(False, frame,cimg)

def judgeShape(tempCnt,cnt):        #マッチシェイプでの判定

    if cnt is not False:            #画像データの輪郭データを取得できている場合
        match = cv2.matchShapes(tempCnt, cnt, cv2.CONTOURS_MATCH_I1, 0)
        if match < differTh:        #類似度がしきい値以下ならOK
            shapeResult = "OK"
            color = (255,0,0)
        else:                       #類似度がしきい値以上ならNG
            shapeResult = "NG"
            color = (0,0,255)
    else:                           #輪郭データが取得できていない場合は合否判別なし
        match = 0
        shapeResult = "ND"
        color = (255,255,255)

    return(shapeResult,match)

def judgeDent(cnt,dentNum,nomalDepthTh,ngDepthTh):          #凹形状により判定する
    if cnt is not False:                                    #画像データの輪郭データを取得できている場合
        hull = cv2.convexHull(cnt,returnPoints = False)     #外接多角形を規定する

        try:
            defects = cv2.convexityDefects(cnt,hull)        #凹み形状のリストを取得

            if defects is not None:
                depthList = []                              #凹みの深さリスト初期化
                for i in range(defects.shape[0]):
                    s,e,f,d = defects[i,0]
                    depthList.append(d)                     #凹みの深さリスト追加
                    start = tuple(cnt[s][0])
                    end = tuple(cnt[e][0])
                    far = tuple(cnt[f][0])
                    if drawDent == True:                                #凹み形状をframeに上書き
                        cv2.line(frame,start,end,[0,255,0],2)           #外接多角形を描画

                        if d > nomalDepthTh:                            #正しい凹み点を描画
                            cv2.circle(frame,far,10,[255,0,0],-1)
                        elif d <= nomalDepthTh and d> ngDepthTh:        #異常な凹み点を描画
                            cv2.circle(frame,far,10,[0,0,255],-1)    

                depthList = sorted(depthList, reverse = True)           #凹み深さを降順にソート

                if len(depthList) < dentNum:                            #凹み形状の数が正規の数より少ない場合はND
                    dentResult = "ND"
                elif len(depthList) == dentNum:                         #凹み形状の数が正規の数と等しい場合
                    if depthList[dentNum - 1] > nomalDepthTh:
                        dentResult = "OK"                               #最も小さい凹みの深さが既定値以上であればOk
                    else:
                        dentResult = "ND"                               #最も小さい凹みの深さが既定値以下であればNG
                else:                                                   #凹み形状の数が正規の数より大きい場合
                    if depthList[dentNum - 1] > nomalDepthTh:           #正規の凹みの最も小さいものが、既定値よりも大きくて
                        if depthList[dentNum] < ngDepthTh:              #正規の凹みの数の次の凹みがNG判定の凹みより小さければOK
                            dentResult = "OK"
                        else:                                           #正規の凹みの数の次の凹みがNG判定の凹みより大きければNG
                            dentResult = "NG"
                    else:                                               #世紀の凹みの最も小さいものが、既定値よりも小さければND
                        dentResult = "ND"
                return(dentResult,frame)
            else:
                dentResult = "ND"
                return(dentResult,frame)

        except cv2.error:
#            print("******cnvexityDefects error catched!")
            dentResult = "ND"
            return(dentResult,frame)

    dentResult = "--"
    print("dentJudgement miss")
    return(dentResult,frame)

def comprehensiveJudge(shapeResult,dentResult):

    comprehensiveResult = "ND"
    if dentResult == "ND":
        comprehnsiveResult = "ND"
        textColor = (255,255,255)

    elif dentResult != "ND":
        if shapeResult == "OK" and dentResult == "OK":
            comprehensiveResult = "OK"
            textColor = (255,0,0)

        else:
            comprehensiveResult = "NG"
            textColor = (0,0,255)
#    print("Comprehensive result = ", comprehensiveResult)
    return(comprehensiveResult,textColor)

def changeThre(key):    #しきい値変更処理
    global th1,th2,binTh,ksize,differTh

    if key == ord("u"): 
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
        binTh += 10
        print("binTh = ",binTh)
    elif key == ord("l"):
        binTh -= 10
        print("binTh = ",binTh)
    elif key == ord("y"):
        ksize += 2
        print("ksize = ",ksize)
    elif key == ord("h"):
        ksize -= 2
        if ksize <= -1:
            ksize = -1
        print("ksize = ",ksize)
    elif key == ord("t"):
        differTh = round(differTh + 0.001,4)
        print("differTh = ",differTh)
    elif key == ord("g"):
        differTh = round(differTh - 0.001,4)
        print("differTh = ",differTh)

#テンプレートの輪郭データを取得
tempCnt,tempCimg = makeTemplateContours()

while True:
    #カメラ画像取得
    ret, frame = capture.read()

    if ret is False:
        raise IOError

    #画像前処理
    frame,gray,binary,edge = preprocess(frame)

    #輪郭データ作成
    cnt,frame,cimg = contours(frame,edge)

    #エッジデータの類似度判定
    shapeResult,match = judgeShape(tempCnt,cnt)

    #凹みデータによる判定
    dentResult,frame = judgeDent(cnt,dentNum,nomalDepthTh,ngDepthTh)

    #総合判定
    comprehensiveResult,color = comprehensiveJudge(shapeResult,dentResult)


    #表示画像に画像ラベル記入
    cv2.putText(tempCimg,"Template",(30,90),cv2.FONT_HERSHEY_SIMPLEX,3.0,(0,255,0),2,cv2.LINE_AA)
    cv2.putText(cimg,comprehensiveResult + " / differ = " + "{:.4f}".format(match),(30,90),cv2.FONT_HERSHEY_SIMPLEX,3.0,color,2,cv2.LINE_AA)
    cv2.putText(frame,"image",(30,90),cv2.FONT_HERSHEY_SIMPLEX,3.0,(0,255,0),2,cv2.LINE_AA)   

    #グレー画像、2値化画像、輪郭画像、テンプレート画像を結合して表示
    binary = cv2.cvtColor(binary,cv2.COLOR_GRAY2RGB)
    concat1 = cv2.vconcat([frame,binary]).astype('uint8')
#    concat1 = cv2.cvtColor(cv2.vconcat([gray,binary]),cv2.COLOR_GRAY2RGB)
    concat2 = cv2.vconcat([tempCimg,cimg]).astype('uint8')
    concat3 = cv2.hconcat([concat1,concat2])
    concat3 = cv2.resize(concat3 , (int(concat3.shape[1]*0.5), int(concat3.shape[0]*0.5)))
    cv2.imshow('result',concat3)

    #キー入力の処理　ESC：終了　　P：テンプレート更新
    key = cv2.waitKey(1)
    if key == 27: #ESC
        break
    elif key == ord("p"):
        cv2.imwrite("Template.jpg",binary)
        tempCnt,tempCimg = makeTemplateContours()
    elif key == ord(";"):
        cv2.imwrite("Concat3.jpg",concat3)
    elif key == ord("r"):
        counter = 0

    if counter < waitCycle:
        counter += 1
    elif counter == waitCycle:
        if comprehensiveResult != "ND":
            print("Comprehensive result = ", comprehensiveResult)
        else:
            print("please adjust camera setting")
        counter += 1

    #キー入力の処理　しきい値変更
    changeThre(key)

capture.release()
cv2.destroyAllWindows()