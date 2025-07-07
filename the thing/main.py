from PyQt5.QtWidgets import QApplication, QFileDialog
import sys
from province_editor_core import MainWindow
    
if __name__ == "__main__":    
    app = QApplication(sys.argv)
    map_path = QFileDialog.getOpenFileName(None, "Select Map Image", "", "Images (*.png *.jpg *.bmp)")[0]

    if map_path:
        print(f"[main] File selected: {map_path}")
        window = MainWindow(map_path)
        window.show()
        sys.exit(app.exec_())
    else:
        print("[main] No file selected. Exiting.")
