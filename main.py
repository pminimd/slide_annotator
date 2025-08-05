from PyQt5.QtWidgets import QApplication
from annotator import VideoAnnotator
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoAnnotator()
    window.show()
    sys.exit(app.exec_())

