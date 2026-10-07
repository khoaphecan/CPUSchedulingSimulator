from __future__ import annotations
from copy import deepcopy
from process_model import Process
from scheduling_result import GanttItem, SchedulingResult

def run_priority(input_processes: list[Process]) -> SchedulingResult:
    processes = deepcopy(input_processes)
    remaining = processes.copy()
    gantt: list[GanttItem] = []
    current_time = 0

    while remaining:
        ready = [p for p in remaining if p.arrival_time <= current_time]
        if not ready:
            next_time = min(p.arrival_time for p in remaining)
            if current_time < next_time:
                gantt.append(
                    GanttItem(
                        process_name="IDLE",
                        start_time=current_time,
                        end_time=next_time,
                    )
                )
            current_time = next_time
            continue

        process = min(ready, key=lambda item: (item.priority, item.arrival_time, item.name))
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
        remaining.remove(process)

    processes.sort(key=lambda process: process.name)
    return SchedulingResult(processes=processes, gantt=gantt)