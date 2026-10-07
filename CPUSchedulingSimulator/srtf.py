from __future__ import annotations
from copy import deepcopy
from process_model import Process
from scheduling_result import GanttItem, SchedulingResult

def run_srtf(input_processes: list[Process]) -> SchedulingResult:
    processes = deepcopy(input_processes)
    if not processes:
        return SchedulingResult(processes=[], gantt=[])

    remaining_time = {p.name: p.burst_time for p in processes}
    first_start: dict[str, int] = {}
    gantt: list[GanttItem] = []
    current_time = 0
    completed = 0

    while completed < len(processes):
        ready = [
            p for p in processes
            if p.arrival_time <= current_time and remaining_time[p.name] > 0
        ]

        if not ready:
            start_time = current_time
            current_time += 1
            if gantt and gantt[-1].process_name == "IDLE" and gantt[-1].end_time == start_time:
                gantt[-1].end_time = current_time
            else:
                gantt.append(
                    GanttItem(
                        process_name="IDLE",
                        start_time=start_time,
                        end_time=current_time,
                    )
                )
            continue

        process = min(
            ready,
            key=lambda item: (remaining_time[item.name], item.arrival_time, item.name),
        )

        if process.name not in first_start:
            first_start[process.name] = current_time

        start_time = current_time
        current_time += 1
        remaining_time[process.name] -= 1

        if gantt and gantt[-1].process_name == process.name and gantt[-1].end_time == start_time:
            gantt[-1].end_time = current_time
        else:
            gantt.append(
                GanttItem(
                    process_name=process.name,
                    start_time=start_time,
                    end_time=current_time,
                )
            )

        if remaining_time[process.name] == 0:
            completed += 1
            process.completion_time = current_time
            process.turnaround_time = process.completion_time - process.arrival_time
            process.waiting_time = process.turnaround_time - process.burst_time
            process.response_time = first_start[process.name] - process.arrival_time

    processes.sort(key=lambda process: process.name)
    return SchedulingResult(processes=processes, gantt=gantt)