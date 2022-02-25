# ワークの輪郭を抽出して、テンプレートとの類似度から合否判定を行う。
#
# t/g　     合否判定のしきい値
# y/h       median blurのしきい値
# u/j       th1
# i/k       th2
# o/l       binTh
# p         テンプレート更新
# ESC       プログラム終了


import cv2
import numpy as np
from PIL import Image as im

#カメラ解像度指定。カメラによって使える解像度は異なる。
WIDTH  = 1280  #320/640/800/1024/1280/1920
HEIGHT = 720  #240/480/600/ 576/ 720/1080

#camera歪みキャリブレーション USBカメラ、1280×720サイズで調整
#カメラ解像度、カメラ変更の場合はcameratestUndist01.pyで係数測定が必要
#https://qiita.com/ReoNagai/items/5da95dea149c66ddbbdd

mtx  = np.array( [[4.88537936e+03,0.0,6.24772642e+02],[0.0,4.84481440e+03,3.54634299e+02],[0.0,0.0,1.0]])
dist = np.array([9.40016759e+00,-7.86181791e+02,3.50155397e-02,-6.47058512e-02,2.08359575e+04])

alpha = 1
newKK, roiSize = cv2.getOptimalNewCameraMatrix(mtx, dist, (WIDTH,HEIGHT), alpha, (WIDTH,HEIGHT))
mapX, mapY = cv2.initUndistortRectifyMap(mtx, dist, None, newKK, (WIDTH,HEIGHT), cv2.CV_32FC1)

#しきい値設定
th1 = 300           #cannyフィルタ用しきい値
th2 = 1000          #cannyフィルタ用しきい値
ksize = 1           #median blur用しきい値 -1でフィルタ不使用
binTh = 250         #binary処理用しきい値
maxValue = 255      #binary処理用しきい値
differTh = 0.03     #類似度判定のしきい値

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
    tempContours, hierarchy = cv2.findContours(edgeTemp,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    #輪郭線データから輪郭のみの画像を描画
    cimg = np.zeros((template.shape[0],template.shape[1],3))
    cimg = cv2.drawContours(cimg, tempContours, 1, (255,255,255), 1)

    return(tempContours[1],cimg)

def preprocess(frame):

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

    return(gray,binary,edge)

def contours(edge):             #輪郭データ作成

    #輪郭線データを取得
    contours, hierarchy = cv2.findContours(edge,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    #黒背景作成
    cimg = np.zeros((edge.shape[0],edge.shape[1],3))

    try:        #輪郭データを得られた場合は、輪郭画像を描画、輪郭データと輪郭画像を返す
        cimg = cv2.drawContours(cimg, contours, 1, (255,255,255), 1)
        return(contours[1],cimg)
    except:     #輪郭データを得られなかった場合
        print("no contours.")
        return(False, cimg)


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
    gray,binary,edge = preprocess(frame)
    gray2 = gray.copy()

    #エッジデータ抽出
    cnt,cimg = contours(edge)
    defe = False
    #エッジデータの類似度判定
    if cnt is not False:    #画像データの輪郭データを取得できている場合
        match = cv2.matchShapes(tempCnt, cnt, cv2.CONTOURS_MATCH_I3, 0)
        far = []

        hull = cv2.convexHull(cnt,returnPoints = False)
        try:
            defects = cv2.convexityDefects(cnt,hull)
#            print(defects)
            defe = True

        except:
            defe = False
#            print("miss")
#        print("start")

        if defects is not None:
            depthList = []
            print("shape = ", defects.shape[0])
            for i in range(defects.shape[0]):

                s,e,f,d = defects[i,0]
                depthList.append(d)
#                print(farList)
#                print(i,s,e,f,d)
                start = tuple(cnt[s][0])
                end = tuple(cnt[e][0])
                far = tuple(cnt[f][0])
                cv2.line(gray2,start,end,[0,255,0],2)
                cv2.circle(gray2,far,5,[0,0,255],-1)
            
#            print(sorted(depthList,reverse=True))

            try:
                if sorted(depthList,reverse=True)[4] > 500:
                    print("NG")
                else:
                    print("OK")
            except:
                print("not exist")

            print("finish-------------------------------")
            cv2.imshow('gray2',gray2)

        if match < differTh:      #類似度がしきい値以下ならOK
            result = "OK"
            color = (255,0,0)
        else:                       #類似度がしきい値以上ならNG
            result = "NG"
            color = (0,0,255)
    else:                   #輪郭データが取得できていない場合は合否判別なし
        match = 0
        result = "--"
        color = (255,255,255)

    #表示画像に画像ラベル記入
    cv2.putText(tempCimg,"Template",(30,90),cv2.FONT_HERSHEY_SIMPLEX,3.0,255,2,cv2.LINE_AA)
    cv2.putText(cimg,result + " / differ = " + "{:.4f}".format(match),(30,90),cv2.FONT_HERSHEY_SIMPLEX,3.0,color,2,cv2.LINE_AA)
    cv2.putText(gray,"image",(30,90),cv2.FONT_HERSHEY_SIMPLEX,3.0,(255),2,cv2.LINE_AA)   

    #グレー画像、2値化画像、輪郭画像、テンプレート画像を結合して表示
    concat1 = cv2.cvtColor(cv2.vconcat([gray,binary]),cv2.COLOR_GRAY2RGB)
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

    #キー入力の処理　しきい値変更
    changeThre(key)

capture.release()
cv2.destroyAllWindows()