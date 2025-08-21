import cv2
import json
from PyQt5.QtWidgets import (
    QMainWindow, QPushButton, QFileDialog,
    QLabel, QMenu, QAction, QMessageBox,
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QDesktopWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage

from timeline_bar import TimelineBar  # 自定义滑动条组件


class VideoAnnotator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("视频分段标注工具")
        
        # 自动最大化窗口
        screen = QDesktopWidget().screenGeometry()
        self.resize(screen.width(), screen.height())
        self.showMaximized()

        # 视频信息
        self.video_path = ""
        self.cap = None
        self.frame_count = 0
        self.current_frame = 0

        # 标注数据
        self.annotations = []
        self.class_colors = {"normal": Qt.black, "put/fetch": Qt.green, "pour": Qt.red, "load_water": Qt.yellow}

        # ---------- 布局 ----------
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # 视频显示 (自动缩放)
        self.frame_label = QLabel()
        self.frame_label.setAlignment(Qt.AlignCenter)
        self.frame_label.setScaledContents(True)  # 自动缩放内容
        layout.addWidget(self.frame_label, stretch=10)

        # 按钮行
        button_layout = QHBoxLayout()
        self.select_btn = QPushButton("选择视频")
        self.save_btn = QPushButton("保存标注")
        button_layout.addWidget(self.select_btn)
        button_layout.addWidget(self.save_btn)
        layout.addLayout(button_layout, stretch=1)

        # 时间轴
        self.timeline = TimelineBar()
        layout.addWidget(self.timeline, stretch=2)

        # 信号绑定
        self.select_btn.clicked.connect(self.select_video)
        self.save_btn.clicked.connect(self.save_annotations)
        self.timeline.frame_selected.connect(self.on_frame_selected)
        self.timeline.right_click_segment.connect(self.set_label_context)

    def select_video(self):
        fname, _ = QFileDialog.getOpenFileName(self, "选择视频", "", "Videos (*.mp4 *.avi *.mov)")
        if fname:
            self.video_path = fname
            self.cap = cv2.VideoCapture(fname)
            self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.annotations.clear()
            self.timeline.set_frame_count(self.frame_count)
            self.timeline.set_annotations(self.annotations)
            self.show_frame(0)

    def show_frame(self, idx):
        if self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = self.cap.read()
            if ret:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
                self.frame_label.setPixmap(QPixmap.fromImage(img).scaled(
                    self.frame_label.size(), Qt.KeepAspectRatio))
                self.current_frame = idx
                self.timeline.set_current_frame(idx)

    def on_frame_selected(self, frame):
        self.show_frame(frame)
        # 添加标注点（如果不是重复）
        if len(self.annotations) == 0 or frame != self.annotations[-1]['start']:
            self.annotations.append({'start': frame, 'end': None, 'label': None})
        self.timeline.set_annotations(self.annotations)

    def set_label_context(self, idx):
        if idx is None or idx >= len(self.annotations) - 1:
            return
        menu = QMenu(self)
        for label in self.class_colors:
            act = QAction(f"设为 {label}", self)
            act.triggered.connect(lambda checked, l=label: self.set_label(idx, l))
            menu.addAction(act)
        menu.exec_(self.mapToGlobal(self.cursor().pos()))

    def set_label(self, idx, label):
        if 0 <= idx < len(self.annotations) - 1:
            self.annotations[idx]['end'] = self.annotations[idx + 1]['start'] - 1
            self.annotations[idx]['label'] = label
            self.timeline.set_annotations(self.annotations)

    def save_annotations(self):
        for i in range(len(self.annotations) - 1):
            if self.annotations[i]['end'] is None:
                self.annotations[i]['end'] = self.annotations[i + 1]['start'] - 1
        out = [seg for seg in self.annotations if seg['label'] is not None]
        fname, _ = QFileDialog.getSaveFileName(self, "保存标注为 JSON", "", "JSON (*.json)")
        if fname:
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(out, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "保存成功", f"已保存 {len(out)} 个标注段到 {fname}")
    
    def keyPressEvent(self, event):
        if not self.cap:
            return

        if event.key() in (Qt.Key_A, Qt.Key_Left):
            new_frame = max(0, self.current_frame - 5)
            self.show_frame(new_frame)
        elif event.key() in (Qt.Key_D, Qt.Key_Right):
            new_frame = min(self.frame_count - 1, self.current_frame + 5)
            self.show_frame(new_frame)

        event.accept()
