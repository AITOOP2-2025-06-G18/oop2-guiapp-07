import numpy as np
import cv2
from my_module.K21999.lecture05_camera_image_capture import MyVideoCapture

def k24044_lecture05_01():

    # カメラキャプチャ実行
    app = MyVideoCapture()
    app.run()

    # 画像をローカル変数に保存
    google_img : cv2.Mat = cv2.imread('images/google.png')
    capture_img : cv2.Mat = app.get_img()

    g_hight, g_width, g_channel = google_img.shape
    c_hight, c_width, c_channel = capture_img.shape
    print(google_img.shape)
    print(capture_img.shape)

    # カメラ画像をグリッド状に配置するために、現在のGoogle画像上の位置を計算
    for x in range(g_width):
        for y in range(g_hight):
            g, b, r = google_img[y, x]
            # もし白色(255,255,255)だったら置き換える
            if (b, g, r) == (255, 255, 255):
                # カメラ画像のグリッド上の位置を計算
                cam_x = x % c_width
                cam_y = y % c_hight
                # カメラ画像のピクセルで置換
                google_img[y, x] = capture_img[cam_y, cam_x]
    
    # 書き込み処理
    cv2.imwrite('output_images/k24044/lecture05_01_k24044.png', google_img)