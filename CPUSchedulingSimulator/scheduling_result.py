from __future__ import annotations
from dataclasses import dataclass
from process_model import Process

@dataclass
class GanttItem:
    process_name: str
    start_time: int
    end_time: int

@dataclass
class SchedulingResult:
    processes: list[Process]
    gantt: list[GanttItem]

    @property
    def average_waiting_time(self) -> float:
        if not self.processes:
            return 0.0
        return sum(p.waiting_time for p in self.processes) / len(self.processes)

    @property
    def average_turnaround_time(self) -> float:
        if not self.processes:
            return 0.0
        return sum(p.turnaround_time for p in self.processes) / len(self.processes)

    @property
    def average_response_time(self) -> float:
        if not self.processes:
            return 0.0
        return sum(p.response_time for p in self.processes) / len(self.processes)