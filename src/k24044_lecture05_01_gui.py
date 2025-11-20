import sys
from pathlib import Path
import cv2
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QPushButton
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
        self.setWindowTitle("画像加工アプリケーション")
        self.setGeometry(100, 100, 1300, 700)
        
        # キーイベントを受け取るためにフォーカスポリシーを設定
        self.setFocusPolicy(Qt.StrongFocus)
        
        # MyVideoCaptureクラスを使ってカメラを初期化
        self.video_capture = MyVideoCapture()
        self.cap = self.video_capture.cap
        
        # 画像データ保持用
        self.current_frame: np.ndarray | None = None
        self.captured_img: np.ndarray | None = None
        self.processed_img: np.ndarray | None = None
        
        # メインウィジェットとレイアウト
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # --- 画像表示エリア（横並び） ---
        image_layout = QHBoxLayout()
        
        # 1. カメラ映像表示用のQLabel
        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setText("カメラ映像")
        self.camera_label.setMinimumSize(600, 450)
        self.camera_label.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        image_layout.addWidget(self.camera_label)
        
        # 2. 加工画像表示用のQLabel
        self.processed_label = QLabel()
        self.processed_label.setAlignment(Qt.AlignCenter)
        self.processed_label.setText("ここに加工画像が表示されます")
        self.processed_label.setMinimumSize(600, 450)
        self.processed_label.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        image_layout.addWidget(self.processed_label)
        
        main_layout.addLayout(image_layout)
        
        # --- 操作ボタンエリア ---
        button_layout = QHBoxLayout()
        
        # 「撮影」ボタン
        self.btn_capture = QPushButton("撮影")
        self.btn_capture.setMinimumHeight(60)
        self.btn_capture.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.btn_capture.clicked.connect(self.capture_photo)
        button_layout.addWidget(self.btn_capture)
        
        # 「画像加工・表示」ボタン
        self.btn_process = QPushButton("画像加工・表示")
        self.btn_process.setMinimumHeight(60)
        self.btn_process.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.btn_process.clicked.connect(self.process_image)
        button_layout.addWidget(self.btn_process)
        
        main_layout.addLayout(button_layout)
        
        # タイマーを設定して定期的にフレームを更新
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # 約30fps
        
    def update_frame(self):
        """カメラからフレームを取得して表示"""
        ret, frame = self.cap.read()
        
        if not ret:
            self.camera_label.setText("カメラからの読み込みに失敗しました")
            return
        
        # 現在のフレームを保持（写真撮影用、加工前の元画像）
        self.current_frame = frame.copy()
        
        # 表示用にコピーを生成して加工
        img = frame.copy()
        
        # ターゲットマークを描画
        rows, cols, _ = img.shape
        center = (int(cols / 2), int(rows / 2))
        cv2.circle(img, center, 30, (0, 0, 255), 3)
        cv2.circle(img, center, 60, (0, 0, 255), 3)
        cv2.line(img, (center[0], center[1] - 80), (center[0], center[1] + 80), (0, 0, 255), 3)
        cv2.line(img, (center[0] - 80, center[1]), (center[0] + 80, center[1]), (0, 0, 255), 3)
        
        # 左右反転（鏡のように表示）
        img = cv2.flip(img, flipCode=1)
        
        # ラベルに表示
        self.display_image_on_label(img, self.camera_label)
    
    def display_image_on_label(self, cv_image: np.ndarray, label: QLabel):
        """OpenCVの画像を指定されたQLabelに表示するヘルパー関数"""
        # BGR -> RGB変換
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        
        # QImage作成
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # QPixmap作成とスケーリング
        pixmap = QPixmap.fromImage(qt_image)
        
        # ラベルのサイズに合わせてスケール
        scaled_pixmap = pixmap.scaled(
            label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        label.setPixmap(scaled_pixmap)

    def keyPressEvent(self, event):
        """キーボードショートカット（Qキーでも撮影可能）"""
        if event.key() == Qt.Key_Q:
            self.capture_photo()
        else:
            super().keyPressEvent(event)
    
    def capture_photo(self):
        """写真を撮影して保存する（加工はしない）"""
        if self.current_frame is None:
            return
        
        # 撮影した画像を保持
        self.captured_img = self.current_frame.copy()
        self.video_capture.captured_img = self.captured_img
        
        # 撮影した画像を保存
        output_dir = project_root / 'output_images' / 'k24044'
        output_dir.mkdir(parents=True, exist_ok=True)
        capture_filepath = str(output_dir / 'camera_capture.png')
        cv2.imwrite(capture_filepath, self.captured_img)
        
        print(f"撮影完了: {capture_filepath}")
        self.processed_label.setText("撮影しました。\n「画像加工・表示」ボタンを押してください。")
    
    def process_image(self):
        """撮影した画像を加工して表示する"""
        if self.captured_img is None:
            self.processed_label.setText("先に「撮影」ボタンを押してください")
            return
        
        # Google画像を読み込む
        google_img_path = project_root / 'images' / 'google.png'
        if not google_img_path.exists():
            self.processed_label.setText("エラー: images/google.png が見つかりません")
            return
            
        google_img = cv2.imread(str(google_img_path))
        if google_img is None:
            self.processed_label.setText("エラー: 画像の読み込みに失敗しました")
            return
        
        capture_img = self.captured_img
        
        g_hight, g_width, g_channel = google_img.shape
        c_hight, c_width, c_channel = capture_img.shape
        
        # ピクセル置換処理
        # (高速化のためnumpyのブロードキャストを使いたいところですが、
        #  元のロジックを尊重してそのまま記述します)
        for x in range(g_width):
            for y in range(g_hight):
                g, b, r = google_img[y, x]
                # 白色の部分をカメラ画像で置き換え
                if (b, g, r) == (255, 255, 255):
                    # カメラ画像のグリッド上の位置を計算
                    cam_x = x % c_width
                    cam_y = y % c_hight
                    # カメラ画像のピクセルで置換
                    google_img[y, x] = capture_img[cam_y, cam_x]
        
        # 加工済み画像を保持
        self.processed_img = google_img.copy()
        
        # --- ここで加工画像を表示 ---
        self.display_image_on_label(self.processed_img, self.processed_label)
        
        # 画像を保存
        self.save_image()
    
    def save_image(self):
        """加工済み画像を保存"""
        if self.processed_img is None:
            return
        
        # 保存先のパスを設定
        output_dir = project_root / 'output_images' / 'k24044'
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = str(output_dir / 'lecture05_01_k24044.png')
        
        cv2.imwrite(filepath, self.processed_img)
        print(f"加工画像を保存しました: {filepath}")
    
    def closeEvent(self, event):
        """終了処理"""
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

