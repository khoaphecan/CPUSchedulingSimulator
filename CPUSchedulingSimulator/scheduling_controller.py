from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox, QLabel, QMessageBox, QPushButton,
    QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
)
from process_model import Process
from scheduling_result import SchedulingResult
from scheduling_service import SchedulingService

class GanttWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.gantt = []
        self.setMinimumHeight(130)

    def set_gantt(self, gantt) -> None:
        self.gantt = list(gantt)
        self.update()

    def clear_gantt(self) -> None:
        self.gantt = []
        self.update()

    def paintEvent(self, event) -> None:
        if not self.gantt:
            return
        painter = QPainter(self)
        try:
            total_time = max(item.end_time for item in self.gantt)
            if total_time <= 0:
                return

            left = 30
            right = 30
            width_available = max(100, self.width() - left - right)
            block_y = 25
            block_height = 55

            colors = [
                QColor(219, 234, 254),
                QColor(220, 252, 231),
                QColor(254, 249, 195),
                QColor(243, 232, 255),
                QColor(255, 228, 230),
                QColor(224, 231, 255),
                QColor(254, 226, 226),
            ]

            process_colors = {}
            color_index = 0

            for item in self.gantt:
                x = left + int(item.start_time / total_time * width_available)
                block_width = max(2, int((item.end_time - item.start_time) / total_time * width_available))

                if item.process_name == "IDLE":
                    color = QColor(229, 231, 235)
                else:
                    if item.process_name not in process_colors:
                        process_colors[item.process_name] = colors[color_index % len(colors)]
                        color_index += 1
                    color = process_colors[item.process_name]

                painter.fillRect(x, block_y, block_width, block_height, color)
                painter.setPen(QPen(QColor(75, 85, 99), 1))
                painter.drawRect(x, block_y, block_width, block_height)
                painter.drawText(x, block_y, block_width, block_height, Qt.AlignmentFlag.AlignCenter, item.process_name)
                painter.drawText(x - 5, block_y + block_height + 22, str(item.start_time))

            painter.drawText(left + width_available - 5, block_y + block_height + 22, str(total_time))
        finally:
            painter.end()


class SchedulingController:
    def __init__(self, page: QWidget) -> None:
        self.page = page
        self.cbo_algorithm = self._find(QComboBox, "cboAlgorithm")
        self.spin_quantum = self._find(QSpinBox, "spinQuantum")
        self.btn_add = self._find(QPushButton, "btnAddProcess")
        self.btn_delete = self._find(QPushButton, "btnDeleteProcess")
        self.btn_load_sample = self._find(QPushButton, "btnLoadSample")
        self.btn_run = self._find(QPushButton, "btnRunScheduling")
        self.btn_step = self._find(QPushButton, "btnStepScheduling")
        self.btn_reset = self._find(QPushButton, "btnResetScheduling")
        self.tbl_input = self._find(QTableWidget, "tblSchedulingInput")
        self.tbl_result = self._find(QTableWidget, "tblSchedulingResult")
        self.gantt_area = self._find(QWidget, "ganttArea")
        self.lbl_avg_turnaround = self._find(QLabel, "lblAverageTurnaround")
        self.lbl_avg_waiting = self._find(QLabel, "lblAverageWaiting")
        self.lbl_avg_response = self._find(QLabel, "lblAverageResponse")
        self.lbl_status = self._find(QLabel, "lblSchedulingStatus")

        self.step_result: SchedulingResult | None = None
        self.step_index = 0

        self.gantt_widget = GanttWidget(self.gantt_area)
        layout = self.gantt_area.layout()
        if layout is None:
            layout = QVBoxLayout(self.gantt_area)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self.gantt_widget)

        self._configure_algorithm()
        self._configure_tables()
        self._connect_events()
        self.load_sample()

    def _find(self, widget_type, object_name: str):
        widget = self.page.findChild(widget_type, object_name)
        if widget is None:
            raise RuntimeError(f"Không tìm thấy objectName '{object_name}' trong cpu_scheduling.ui")
        return widget

    def _configure_algorithm(self) -> None:
        self.cbo_algorithm.clear()
        self.cbo_algorithm.addItems(["FCFS", "SJF", "SRTF", "Round Robin", "Priority"])
        self.cbo_algorithm.setCurrentText("FCFS")
        self.spin_quantum.setRange(1, 100)
        self.spin_quantum.setValue(3)
        self.spin_quantum.setEnabled(False)

    def _configure_tables(self) -> None:
        self.tbl_input.setColumnCount(4)
        self.tbl_input.setHorizontalHeaderLabels(["Process", "Arrival Time", "Burst Time", "Priority"])
        self.tbl_input.setAlternatingRowColors(True)
        self.tbl_input.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.SelectedClicked | QTableWidget.EditTrigger.AnyKeyPressed
        )
        self.tbl_input.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_input.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tbl_input.raise_()
        self.tbl_result.setColumnCount(8)
        self.tbl_result.setHorizontalHeaderLabels([
            "Process", "Arrival", "Burst", "Priority",
            "Completion", "Turnaround", "Waiting", "Response"
        ])
        self.tbl_result.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_result.setAlternatingRowColors(True)

    def _connect_events(self) -> None:
        self.btn_add.clicked.connect(self.add_process)
        self.btn_delete.clicked.connect(self.delete_process)
        self.btn_load_sample.clicked.connect(self.load_sample)
        self.btn_run.clicked.connect(self.run_all)
        self.btn_step.clicked.connect(self.run_step)
        self.btn_reset.clicked.connect(self.reset)
        self.cbo_algorithm.currentTextChanged.connect(self.algorithm_changed)
        self.spin_quantum.valueChanged.connect(self.invalidate_step)
        self.tbl_input.itemChanged.connect(self.invalidate_step)

    def algorithm_changed(self, algorithm: str) -> None:
        self.spin_quantum.setEnabled(algorithm == "Round Robin")
        self.invalidate_step()
        self.lbl_status.setText(f"Trạng thái: Đã chọn {algorithm}")

    def invalidate_step(self, *args) -> None:
        self.step_result = None
        self.step_index = 0

    def add_process(self) -> None:
        row = self.tbl_input.rowCount()
        self.tbl_input.insertRow(row)
        values = [f"P{row + 1}", "0", "1", "1"]
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tbl_input.setItem(row, column, item)
        self.invalidate_step()
        self.lbl_status.setText("Trạng thái: Đã thêm Process")

    def delete_process(self) -> None:
        row = self.tbl_input.currentRow()
        if row < 0:
            QMessageBox.information(self.page, "Xóa Process", "Hãy chọn một Process cần xóa.")
            return
        self.tbl_input.removeRow(row)
        self.invalidate_step()
        self.lbl_status.setText("Trạng thái: Đã xóa Process")

    def load_sample(self) -> None:
        sample = [
            ("P1", 0, 10, 3),
            ("P2", 2, 5, 1),
            ("P3", 4, 3, 4),
            ("P4", 6, 7, 2),
        ]
        self.tbl_input.blockSignals(True)
        try:
            self.tbl_input.setRowCount(0)
            for values in sample:
                row = self.tbl_input.rowCount()
                self.tbl_input.insertRow(row)
                for column, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.tbl_input.setItem(row, column, item)
        finally:
            self.tbl_input.blockSignals(False)

        self.cbo_algorithm.setCurrentText("FCFS")
        self.spin_quantum.setValue(3)
        self.clear_output()
        self.invalidate_step()
        self.lbl_status.setText("Trạng thái: Đã nạp dữ liệu mẫu")

    def read_processes(self) -> list[Process]:
        processes: list[Process] = []
        names: set[str] = set()

        for row in range(self.tbl_input.rowCount()):
            name_item = self.tbl_input.item(row, 0)
            arrival_item = self.tbl_input.item(row, 1)
            burst_item = self.tbl_input.item(row, 2)
            priority_item = self.tbl_input.item(row, 3)

            if name_item is None or arrival_item is None or burst_item is None:
                raise ValueError(f"Dòng {row + 1} chưa nhập đủ dữ liệu.")

            name = name_item.text().strip()
            if not name:
                raise ValueError(f"Dòng {row + 1}: Process không được để trống.")
            if name in names:
                raise ValueError(f"Process '{name}' bị trùng.")
            names.add(name)

            try:
                arrival = int(arrival_item.text())
                burst = int(burst_item.text())
                priority = int(priority_item.text()) if (priority_item and priority_item.text().strip()) else 1
            except ValueError as error:
                raise ValueError(f"Dòng {row + 1}: Arrival, Burst và Priority phải là số nguyên.") from error

            if arrival < 0:
                raise ValueError(f"({name}): Arrival Time không được âm.")
            if burst <= 0:
                raise ValueError(f"({name}): Burst Time phải > 0.")
            if priority <= 0:
                raise ValueError(f"({name}): Priority phải > 0.")

            processes.append(Process(name=name, arrival_time=arrival, burst_time=burst, priority=priority))

        if not processes:
            raise ValueError("Chưa có Process nào.")
        return processes

    def calculate(self) -> SchedulingResult:
        return SchedulingService.run(
            algorithm=self.cbo_algorithm.currentText(),
            processes=self.read_processes(),
            quantum=self.spin_quantum.value(),
        )

    def run_all(self) -> None:
        try:
            result = self.calculate()
            self.display_result(result)
            self.gantt_widget.set_gantt(result.gantt)
            self.display_average(result)
            self.step_result = result
            self.step_index = len(result.gantt)
            algorithm = self.cbo_algorithm.currentText()
            if algorithm == "Round Robin":
                self.lbl_status.setText(f"Trạng thái: Hoàn thành {algorithm}, Quantum = {self.spin_quantum.value()}")
            else:
                self.lbl_status.setText(f"Trạng thái: Hoàn thành {algorithm}")
        except Exception as error:
            QMessageBox.critical(self.page, "Lỗi CPU Scheduling", str(error))
            self.lbl_status.setText("Trạng thái: Có lỗi")

    def run_step(self) -> None:
        try:
            if self.step_result is None:
                self.step_result = self.calculate()
                self.step_index = 0
                self.tbl_result.setRowCount(0)
                self.gantt_widget.clear_gantt()
                self.reset_average()

            gantt = self.step_result.gantt
            if self.step_index >= len(gantt):
                QMessageBox.information(self.page, "Step", "Đã chạy hết các bước.")
                return

            self.step_index += 1
            visible_gantt = gantt[:self.step_index]
            self.gantt_widget.set_gantt(visible_gantt)
            current_item = visible_gantt[-1]
            self.lbl_status.setText(
                f"Trạng thái: Step {self.step_index}/{len(gantt)}: "
                f"{current_item.process_name} [{current_item.start_time} -> {current_item.end_time}]"
            )

            if self.step_index == len(gantt):
                self.display_result(self.step_result)
                self.display_average(self.step_result)
                self.lbl_status.setText(f"Trạng thái: Hoàn thành {self.cbo_algorithm.currentText()}")
        except Exception as error:
            QMessageBox.critical(self.page, "Lỗi Step", str(error))
            self.lbl_status.setText("Trạng thái: Có lỗi")

    def display_result(self, result: SchedulingResult) -> None:
        self.tbl_result.setRowCount(len(result.processes))
        for row, process in enumerate(result.processes):
            values = [
                process.name,
                process.arrival_time,
                process.burst_time,
                process.priority,
                process.completion_time,
                process.turnaround_time,
                process.waiting_time,
                process.response_time,
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tbl_result.setItem(row, column, item)
        self.tbl_result.resizeColumnsToContents()

    def display_average(self, result: SchedulingResult) -> None:
        self.lbl_avg_waiting.setText(f"Waiting trung bình: {result.average_waiting_time:.2f}")
        self.lbl_avg_turnaround.setText(f"Turnaround trung bình: {result.average_turnaround_time:.2f}")
        self.lbl_avg_response.setText(f"Response trung bình: {result.average_response_time:.2f}")

    def reset_average(self) -> None:
        self.lbl_avg_waiting.setText("Waiting trung bình: 0")
        self.lbl_avg_turnaround.setText("Turnaround trung bình: 0")
        self.lbl_avg_response.setText("Response trung bình: 0")

    def clear_output(self) -> None:
        self.tbl_result.setRowCount(0)
        self.gantt_widget.clear_gantt()
        self.reset_average()

    def reset(self) -> None:
        self.tbl_input.blockSignals(True)
        try:
            self.tbl_input.setRowCount(0)
        finally:
            self.tbl_input.blockSignals(False)

        self.cbo_algorithm.setCurrentText("FCFS")
        self.spin_quantum.setValue(3)
        self.clear_output()
        self.step_result = None
        self.step_index = 0
        self.lbl_status.setText("Trạng thái: Sẵn sàng")
