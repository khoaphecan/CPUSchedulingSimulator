from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Process:
    name: str
    arrival_time: int
    burst_time: int
    priority: int = 1
    completion_time: int = 0
    turnaround_time: int = 0
    waiting_time: int = 0
    response_time: int = 0    
