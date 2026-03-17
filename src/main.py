import portalocker
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QCoreApplication, QTranslator
from gui.main_window import MainWindow
from config import config


lock_file = "mcsr_auto_clip.lock"

def check_single_instance():
    fp = open(lock_file, "w")
    try:
        portalocker.lock(fp, portalocker.LOCK_EX | portalocker.LOCK_NB)
        return fp
    except portalocker.exceptions.LockException:
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Icon.Critical)
        error_box.setWindowTitle(QCoreApplication.translate("main", "MCSR AUTO CLIP Running Error"))
        error_box.setText(QCoreApplication.translate("main", "Program is already running. Do not start it again."))
        error_box.exec()
        sys.exit()


def main():
    app = QApplication(sys.argv)

    if (qm_path := config.translation_dir / f'{config.lang}.qm').exists():
        translator = QTranslator()
        translator.load(str(qm_path))
        app.installTranslator(translator)

    fp = check_single_instance()
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
