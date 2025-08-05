from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen


class TimelineBar(QWidget):
    frame_selected = pyqtSignal(int)
    right_click_segment = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(30)
        self.annotations = []  # [{'start':int, 'end':int, 'label':str}]
        self.frame_count = 1
        self.current_frame = 0
        self.class_colors = {"A": Qt.green, "B": Qt.red, "C": Qt.yellow}

    def set_frame_count(self, count):
        self.frame_count = max(1, count)
        self.update()

    def set_annotations(self, annotations):
        self.annotations = annotations
        self.update()

    def set_current_frame(self, frame):
        self.current_frame = frame
        self.update()

    def mousePressEvent(self, event):
        ratio = event.x() / self.width()
        frame = int(ratio * self.frame_count)

        if event.button() == Qt.LeftButton:
            self.frame_selected.emit(frame)
        elif event.button() == Qt.RightButton:
            idx = self.find_segment_by_frame(frame)
            self.right_click_segment.emit(idx)

    def find_segment_by_frame(self, frame):
        for i in range(len(self.annotations) - 1):
            if self.annotations[i]['start'] <= frame < self.annotations[i + 1]['start']:
                return i
        return len(self.annotations) - 1 if self.annotations else None

    def paintEvent(self, event):
        painter = QPainter(self)

        # draw background
        painter.fillRect(self.rect(), Qt.lightGray)

        # draw colored segments
        for ann in self.annotations:
            if 'label' in ann and ann['label']:
                color = QColor(self.class_colors[ann['label']])
                start_x = int(ann['start'] / self.frame_count * self.width())
                end_x = int(ann.get('end', self.frame_count - 1) / self.frame_count * self.width())
                painter.fillRect(start_x, 0, end_x - start_x, self.height(), color)

        # draw annotation points
        pen = QPen(Qt.black, 2)
        painter.setPen(pen)
        for ann in self.annotations:
            x = int(ann['start'] / self.frame_count * self.width())
            painter.drawLine(x, 0, x, self.height())

        # draw current frame pointer
        pointer_x = int(self.current_frame / self.frame_count * self.width())
        pen = QPen(Qt.blue, 2)
        painter.setPen(pen)
        painter.drawLine(pointer_x, 0, pointer_x, self.height())

        painter.end()

