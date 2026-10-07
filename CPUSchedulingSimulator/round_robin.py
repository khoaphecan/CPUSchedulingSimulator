from __future__ import annotations
from collections import deque
from copy import deepcopy
from process_model import Process
from scheduling_result import GanttItem, SchedulingResult

def run_round_robin(input_processes: list[Process], quantum: int) -> SchedulingResult:
    if quantum <= 0:
        raise ValueError("Quantum phải lớn hơn 0.")

    processes = deepcopy(input_processes)
    processes.sort(key=lambda process: (process.arrival_time, process.name))

    remaining_time = {p.name: p.burst_time for p in processes}
    first_start: dict[str, int] = {}
    ready_queue = deque()
    gantt: list[GanttItem] = []
    current_time = 0
    next_index = 0
    completed = 0

    while completed < len(processes):
        while next_index < len(processes) and processes[next_index].arrival_time <= current_time:
            ready_queue.append(processes[next_index])
            next_index += 1

        if not ready_queue:
            if next_index >= len(processes):
                break
            next_time = processes[next_index].arrival_time
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

        process = ready_queue.popleft()
        if process.name not in first_start:
            first_start[process.name] = current_time

        start_time = current_time
        run_time = min(quantum, remaining_time[process.name])
        current_time += run_time
        remaining_time[process.name] -= run_time

        gantt.append(
            GanttItem(
                process_name=process.name,
                start_time=start_time,
                end_time=current_time,
            )
        )

        while next_index < len(processes) and processes[next_index].arrival_time <= current_time:
            ready_queue.append(processes[next_index])
            next_index += 1

        if remaining_time[process.name] > 0:
            ready_queue.append(process)
        else:
            completed += 1
            process.completion_time = current_time
            process.turnaround_time = process.completion_time - process.arrival_time
            process.waiting_time = process.turnaround_time - process.burst_time
            process.response_time = first_start[process.name] - process.arrival_time

    processes.sort(key=lambda process: process.name)
    return SchedulingResult(processes=processes, gantt=gantt)