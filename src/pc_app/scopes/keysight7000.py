from .keysight import KeysightScope
import pyvisa


# ----------------------------
# Keysight / Agilent 7000 Scope
# ----------------------------
class Keysight7000Scope(KeysightScope):
    def get_screenshot_png(self, color: bool, inverted: bool) -> bytes:

        palette = "COLor" if color else "GRAYscale"
        inksaver = "ON" if inverted else "OFF"

        # ---------- Binary mode ----------
        self.scope.write_termination = ''
        self.scope.read_termination = ''
        old_timeout = self.scope.timeout
        self.scope.timeout = 10000

        # ---------- Apply InkSaver ----------
        self.scope.write(f":HARDcopy:INKSaver {inksaver}")

        # ---------- Request screen dump ----------
        raw = self.scope.query_binary_values(
            f":DISPlay:DATA? PNG,SCReen,{palette}",
            datatype='B',
            container=bytes
        )

        # ---------- Restore ASCII mode ----------
        self.scope.write_termination = '\n'
        self.scope.read_termination = '\n'
        self.scope.timeout = old_timeout

        # ---------- Strip IEEE-488.2 binary header ----------
        if raw.startswith(b"#"):
            n = int(raw[1:2])
            length = int(raw[2:2 + n])
            data = raw[2 + n:2 + n + length]
        else:
            data = raw

        return data
