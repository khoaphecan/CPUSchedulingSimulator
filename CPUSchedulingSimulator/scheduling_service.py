from __future__ import annotations
from fcfs import run_fcfs
from priority import run_priority
from process_model import Process
from round_robin import run_round_robin
from scheduling_result import SchedulingResult
from sjf import run_sjf
from srtf import run_srtf

class SchedulingService:
    @staticmethod
    def run(algorithm: str, processes: list[Process], quantum: int = 3) -> SchedulingResult:
        name = algorithm.strip().lower()
        if name == "fcfs":
            return run_fcfs(processes)
        if name == "sjf":
            return run_sjf(processes)
        if name == "srtf":
            return run_srtf(processes)
        if name in {"round robin", "rr"}:
            return run_round_robin(processes, quantum)
        if name == "priority":
            return run_priority(processes)
        raise ValueError(f"Không hỗ trợ thuật toán '{algorithm}'.")
