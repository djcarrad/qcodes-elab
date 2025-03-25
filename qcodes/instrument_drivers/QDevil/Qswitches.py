from QSwitch_elab import QSwitch
import numpy as np
from typing import (
    Tuple, Sequence, List, Dict, Set, Union, Optional)

relays_per_line = 9
relay_lines = 24

State = Sequence[Tuple[int, int]]

OneOrMore = Union[str, Sequence[str]]

class QSwitches():
    def __init__(self, qswitch: list[QSwitch]):
        self.qswitch = qswitch
        # self.num_of_qswitches = len(qswitch)
        self._set_default_names()



    def reset(self) -> None:
        self.qswitch[0].reset()
        self.qswitch[1].reset()

    # -----------------------------------------------------------------------
    # Direct manipulation of the relays
    # -----------------------------------------------------------------------

    def open_relay(self, line: int, tap: int) -> None:
        if line <= 24:
            self.qswitch[0].open_relay(line, tap)
        else:
            self.qswitch[1].open_relay(line-26, tap)
    
    def close_relay(self, line: int, tap: int) -> None:
        if line <= 24:
            self.qswitch[0].close_relay(line, tap)
        else:
            self.qswitch[1].close_relay(line-26, tap)


    def close_relays(self, relays: State) -> None:
        for line, tap in relays:
            if line <=24:
                self.qswitch[0].close_relay(line, tap)
            else:
                self.qswitch[1].close_relay(line-26, tap)

    def open_relays(self, relays: State) -> None:
        for line, tap in relays:
            if line <=24:
                self.qswitch[0].open_relay(line, tap)
            else:
                self.qswitch[1].open_relay(line-26, tap)


    
    # -----------------------------------------------------------------------
    # Manipulation by name
    # -----------------------------------------------------------------------

    def arrange(self, breakouts: Optional[Dict[str, int]] = None,
                lines: Optional[Dict[str, int]] = None) -> None:
        breakouts1 = {}
        breakouts2 = {}

        lines1 = {}
        lines2 = {}

        if breakouts:
            for name, number in breakouts.items():
                self._tap_names[name] = number
                if number <= 24:
                    breakouts1[name] = number
                else:
                    breakouts2[name] = number - 26

        if lines:
            for name, number in lines.items():
                self._line_names[name] = number
                if number <= 24:
                    lines1[name] = number
                else:
                    lines2[name] = number - 26

        self.qswitch[0].arrange(breakouts1, lines1)
        self.qswitch[1].arrange(breakouts2, lines2)

    def breakout(self, line : str, tap: str) -> None:
        if self._to_line(line) <= 24:
            self.qswitch[0].breakout(self._to_line(line), self._to_tap(tap))
        else:
            self.qswitch[1].breakout(self._to_line(line)-26, self._to_tap(tap))

    
    def ground(self, lines: OneOrMore) -> None:
        lines = self._to_line(lines)
        for line in lines:
            if line <= 24:
                self.qswitch[0].ground(line)
            else:
                self.qswitch[1].ground(line-26)

    def connect(self, lines: OneOrMore) -> None:
        lines = self._to_line(lines)
        for line in lines:
            if line <= 24:
                self.qswitch[0].connect(line)
            else:
                self.qswitch[1].connect(line-26)


    def lineFloat(self, lines: OneOrMore) -> None:
        lines = self._to_line(lines)
        for line in lines:
            if line <= 24:
                self.qswitch[0].lineFloat(line)
            else:
                self.qswitch[1].lineFloat(line-26)










    def _set_default_names(self) -> None:
        lines = np.concatenate((np.arange(1, relay_lines), np.arange(26, 26 + relay_lines)))
        taps = range(1, relays_per_line)
        self._line_names = dict(zip(map(str, lines), lines))
        self._tap_names = dict(zip(map(str, taps), taps))


    def _to_line(self, name: str) -> int:
        try:
            return self._line_names[name]
        except KeyError:
            raise ValueError(f'Unknown line "{name}"')

    def _to_tap(self, name: str) -> int:
        try:
            return self._tap_names[name]
        except KeyError:
            raise ValueError(f'Unknown tap "{name}"')