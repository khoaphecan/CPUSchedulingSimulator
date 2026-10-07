from __future__ import annotations
from copy import deepcopy
from process_model import Process
from scheduling_result import GanttItem, SchedulingResult

def run_fcfs(input_processes: list[Process]) -> SchedulingResult:
    processes = deepcopy(input_processes)
    processes.sort(key=lambda process: (process.arrival_time, process.name))

    current_time = 0
    gantt: list[GanttItem] = []

    for process in processes:
        if current_time < process.arrival_time:
            gantt.append(
                GanttItem(
                    process_name="IDLE",
                    start_time=current_time,
                    end_time=process.arrival_time,
                )
            )
            current_time = process.arrival_time

        start_time = current_time
        process.response_time = start_time - process.arrival_time
        current_time += process.burst_time
        process.completion_time = current_time
        process.turnaround_time = process.completion_time - process.arrival_time
        process.waiting_time = process.turnaround_time - process.burst_time

        gantt.append(
            GanttItem(
                process_name=process.name,
                start_time=start_time,
                end_time=current_time,
            )
        )

    processes.sort(key=lambda process: process.name)
    return SchedulingResult(processes=processes, gantt=gantt)