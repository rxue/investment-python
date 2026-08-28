import math
from typing import NamedTuple


class Range(NamedTuple):
    start: float
    end: float
    def has(self, value:float) -> bool:
        start = self.start if self.start else 0
        end = self.end if self.end else math.inf
        return start <= value <= end
