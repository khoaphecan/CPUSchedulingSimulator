import sys
from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication
from scheduling_controller import SchedulingController

def main() -> None:
    app = QApplication(sys.argv)
    ui_file = QFile("cpu_scheduling.ui")
    if not ui_file.open(QFile.OpenModeFlag.ReadOnly):
        raise RuntimeError("Không thể mở file cpu_scheduling.ui")

    loader = QUiLoader()
    window = loader.load(ui_file)
    ui_file.close()

    if window is None:
        raise RuntimeError("Không thể tải giao diện cpu_scheduling.ui")

    controller = SchedulingController(window)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()