import portalocker
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox

from gui.main_window import MainWindow


lock_file = "mcsr_auto_clip.lock"

def check_single_instance():
    fp = open(lock_file, "w")
    try:
        portalocker.lock(fp, portalocker.LOCK_EX | portalocker.LOCK_NB)
        return fp
    except portalocker.exceptions.LockException:
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Icon.Critical)
        error_box.setWindowTitle("MCSR AUTO CLIP 运行错误")
        error_box.setText("程序已在运行中。请检查后台进程或任务栏，不要重复启动。")
        error_box.exec()
        sys.exit()


def main():
    app = QApplication(sys.argv)
    fp = check_single_instance()
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
