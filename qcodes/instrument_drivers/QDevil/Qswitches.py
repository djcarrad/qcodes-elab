from QSwitch_elab import QSwitch

class QSwitches():
    def __init__(self, qswitch: list[QSwitch]):
        self.qswitch = qswitch
        # self.num_of_qswitches = len(qswitch)

    def arrange(self, breakouts: Optional[Dict[str, int]] = None,
                lines: Optional[Dict[str, int]] = None) -> None:
        breakouts1 = {}
        breakouts2 = {}

        lines1 = {}
        lines2 = {}
        
        for name, number in breakouts.items():
            if number <= 24:
                breakouts1[name] = number
            else:
                breakouts2[name] = number - 26

        for name, number in lines.items():
            if number <= 24:
                lines1[name] = number
            else:
                lines2[name] = number - 26

        self.qswitch[0].arrange(breakouts1, lines1)
        self.qswitch[1].arrange(breakouts2, lines2)

    def breakout(self)

        
