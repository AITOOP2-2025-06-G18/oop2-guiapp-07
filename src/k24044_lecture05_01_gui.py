import sys
from pathlib import Path
import cv2
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QPushButton, QHBoxLayout
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ★ここで別ファイルの MyVideoCapture クラスを読み込んでいます（今まで通り）
from my_module.K21999.lecture05_camera_image_capture import MyVideoCapture


class Lecture05GUI(QMainWindow):
    """lecture05_01をGUIアプリケーション化したクラス"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("画像加工アプリケーション")
        self.setGeometry(100, 100, 1200, 850)
        
        self.setFocusPolicy(Qt.StrongFocus)
        
        # MyVideoCaptureクラス（別ファイル）を使ってカメラを初期化
        self.video_capture = MyVideoCapture()
        self.cap = self.video_capture.cap
        
        # 現在のフレームを保持
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
        
        # --- ボタン配置エリア ---
        button_layout = QHBoxLayout()
        
        # 撮影ボタン
        self.capture_btn = QPushButton("撮影")
        self.capture_btn.setMinimumHeight(50)
        self.capture_btn.clicked.connect(self.capture_photo)
        button_layout.addWidget(self.capture_btn)
        
        # 画像加工・表示ボタン
        self.process_btn = QPushButton("画像加工・表示")
        self.process_btn.setMinimumHeight(50)
        self.process_btn.clicked.connect(self.process_image)
        button_layout.addWidget(self.process_btn)
        
        main_layout.addLayout(button_layout)
        # ----------------------
        
        # タイマーを設定して定期的にフレームを更新
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)
        
    def update_frame(self):
        """カメラからフレームを取得して表示"""
        ret, frame = self.cap.read()
        
        if not ret:
            self.camera_label.setText("カメラからの読み込みに失敗しました")
            return
        
        self.current_frame = frame.copy()
        img: np.ndarray = np.copy(frame)
        
        # ターゲットマークの描画
        rows, cols, _ = img.shape
        center = (int(cols / 2), int(rows / 2))
        img = cv2.circle(img, center, 30, (0, 0, 255), 3)
        img = cv2.circle(img, center, 60, (0, 0, 255), 3)
        img = cv2.line(img, (center[0], center[1] - 80), (center[0], center[1] + 80), (0, 0, 255), 3)
        img = cv2.line(img, (center[0] - 80, center[1]), (center[0] + 80, center[1]), (0, 0, 255), 3)
        
        img = cv2.flip(img, flipCode=1)
        rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(
            self.camera_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.camera_label.setPixmap(scaled_pixmap)
    
    def capture_photo(self):
        """撮影ボタンが押されたときの処理"""
        if self.current_frame is None:
            return
        
        self.captured_img = self.current_frame.copy()
        self.video_capture.captured_img = self.captured_img
        
        output_dir = project_root / 'output_images' / 'k24044'
        output_dir.mkdir(parents=True, exist_ok=True)
        capture_filepath = str(output_dir / 'camera_capture.png')
        cv2.imwrite(capture_filepath, self.captured_img)
        
        print("撮影が完了しました。")
        # ここでの process_image 呼び出しは削除済み（ボタン分離のため）
    
    def process_image(self):
        """画像加工ボタンが押されたときの処理"""
        if self.captured_img is None:
            print("先に撮影を行ってください。")
            return
        
        google_img_path = project_root / 'images' / 'google.png'
        google_img: cv2.Mat = cv2.imread(str(google_img_path))
        
        if google_img is None:
            print("Google画像の読み込みに失敗しました。")
            return
        
        capture_img: cv2.Mat = self.captured_img
        g_hight, g_width, g_channel = google_img.shape
        c_hight, c_width, c_channel = capture_img.shape
        
        for x in range(g_width):
            for y in range(g_hight):
                g, b, r = google_img[y, x]
                if (b, g, r) == (255, 255, 255):
                    cam_x = x % c_width
                    cam_y = y % c_hight
                    google_img[y, x] = capture_img[cam_y, cam_x]
        
        self.processed_img = google_img.copy()
        self.save_image()
        print("画像の加工と保存が完了しました。")
    
    def save_image(self):
        """加工済み画像を保存"""
        if self.processed_img is None:
            return
        
        output_dir = project_root / 'output_images' / 'k24044'
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = str(output_dir / 'lecture05_01_k24044.png')
        cv2.imwrite(filepath, self.processed_img)
    
    def closeEvent(self, event):
        """ウィンドウを閉じる際の処理"""
        self.timer.stop()
        if hasattr(self.video_capture, 'cap') and self.video_capture.cap.isOpened():
            self.video_capture.cap.release()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = Lecture05GUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()