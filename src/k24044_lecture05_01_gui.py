import sys
from pathlib import Path
import cv2
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from my_module.K21999.lecture05_camera_image_capture import MyVideoCapture


class Lecture05GUI(QMainWindow):
    """lecture05_01をGUIアプリケーション化したクラス"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("画像加工アプリケーション (Qキーで写真撮影)")
        self.setGeometry(100, 100, 1200, 800)
        
        # キーイベントを受け取るためにフォーカスポリシーを設定
        self.setFocusPolicy(Qt.StrongFocus)
        
        # MyVideoCaptureクラスを使ってカメラを初期化
        self.video_capture = MyVideoCapture()
        self.cap = self.video_capture.cap
        
        # 現在のフレームを保持（写真撮影用）
        self.current_frame: np.ndarray | None = None
        self.captured_img: np.ndarray | None = None
        self.processed_img: np.ndarray | None = None
        
        # 中央ウィジェットとレイアウトを設定
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # カメラ映像表示用のQLabel
        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setText("カメラを初期化中...")
        self.camera_label.setMinimumHeight(400)
        main_layout.addWidget(self.camera_label)
        
        # 加工済み画像表示用のQLabel
        self.processed_label = QLabel()
        self.processed_label.setAlignment(Qt.AlignCenter)
        self.processed_label.setText("Qキーで写真を撮影してください")
        self.processed_label.setMinimumHeight(400)
        main_layout.addWidget(self.processed_label)
        
        # タイマーを設定して定期的にフレームを更新
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # 約30fps (33ms間隔)
        
    def update_frame(self):
        """カメラからフレームを取得して表示"""
        ret, frame = self.cap.read()
        
        if not ret:
            self.camera_label.setText("カメラからの読み込みに失敗しました")
            return
        
        # 現在のフレームを保持（写真撮影用、加工前の元画像）
        self.current_frame = frame.copy()
        
        # 加工するともとの画像が保存できないのでコピーを生成
        img: np.ndarray = np.copy(frame)
        
        # 画像の中心を示すターゲットマークを描画（MyVideoCaptureのrun()メソッドを参考）
        rows, cols, _ = img.shape
        center = (int(cols / 2), int(rows / 2))
        img = cv2.circle(img, center, 30, (0, 0, 255), 3)
        img = cv2.circle(img, center, 60, (0, 0, 255), 3)
        img = cv2.line(img, (center[0], center[1] - 80), (center[0], center[1] + 80), (0, 0, 255), 3)
        img = cv2.line(img, (center[0] - 80, center[1]), (center[0] + 80, center[1]), (0, 0, 255), 3)
        
        # 左右反転（顔を撮るときは左右反転しておくとよい）
        img = cv2.flip(img, flipCode=1)
        
        # OpenCVのBGR画像をRGBに変換
        rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # NumPy配列をQImageに変換
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # QPixmapに変換してQLabelに表示
        pixmap = QPixmap.fromImage(qt_image)
        
        # ラベルのサイズに合わせてスケール
        scaled_pixmap = pixmap.scaled(
            self.camera_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.camera_label.setPixmap(scaled_pixmap)
    
    def keyPressEvent(self, event):
        """キーが押されたときの処理"""
        if event.key() == Qt.Key_Q:
            self.capture_photo()
        else:
            super().keyPressEvent(event)
    
    def capture_photo(self):
        """写真を撮影（k24044_lecture05_01.pyと同じ動作）"""
        if self.current_frame is None:
            return
        
        # 撮影した画像を保存
        self.captured_img = self.current_frame.copy()
        self.video_capture.captured_img = self.captured_img
        
        # 自動的に画像を加工
        self.process_image()
    
    def process_image(self):
        """画像を加工（k24044_lecture05_01.pyの処理）"""
        if self.captured_img is None:
            return
        
        # Google画像を読み込む
        google_img_path = project_root / 'images' / 'google.png'
        google_img: cv2.Mat = cv2.imread(str(google_img_path))
        
        if google_img is None:
            return
        
        capture_img: cv2.Mat = self.captured_img
        
        g_hight, g_width, g_channel = google_img.shape
        c_hight, c_width, c_channel = capture_img.shape
        
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
        
        # 加工済み画像を保存
        self.processed_img = google_img.copy()
        
        # 加工済み画像を表示
        self.display_processed_image(google_img)
        
        # 自動的に保存
        self.save_image()
    
    def display_processed_image(self, img: np.ndarray):
        """加工済み画像を表示"""
        # OpenCVのBGR画像をRGBに変換
        rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # NumPy配列をQImageに変換
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # QPixmapに変換してQLabelに表示
        pixmap = QPixmap.fromImage(qt_image)
        
        # ラベルのサイズに合わせてスケール
        scaled_pixmap = pixmap.scaled(
            self.processed_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.processed_label.setPixmap(scaled_pixmap)
    
    def save_image(self):
        """加工済み画像を保存"""
        if self.processed_img is None:
            return
        
        # 保存先のパスを設定
        output_dir = project_root / 'output_images' / 'k24044'
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = str(output_dir / 'lecture05_01_k24044.png')
        
        # 画像を保存
        cv2.imwrite(filepath, self.processed_img)
    
    def closeEvent(self, event):
        """ウィンドウを閉じる際の処理"""
        self.timer.stop()
        # MyVideoCaptureのリソースを解放
        if hasattr(self.video_capture, 'cap') and self.video_capture.cap.isOpened():
            self.video_capture.cap.release()
        event.accept()


def main():
    """メイン関数"""
    app = QApplication(sys.argv)
    
    window = Lecture05GUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

