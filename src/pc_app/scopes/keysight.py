from .base import BaseScope
import pyvisa


# ----------------------------
# Keysight / Agilent Scope
# ----------------------------
class KeysightScope(BaseScope):

    def identify(self, enable: bool):
        if enable:
            self.scope.write(':SYST:DSP "FOOT SWITCH\nIDENTIFIER"')
        else:
            self.scope.write(':SYST:DSP ""')

    def run(self):
        self.scope.write(":RUN")
        self.running = True

    def stop(self):
        self.scope.write(":STOP")
        self.running = False

    def single(self):
        self.scope.write(":SINGLE")

    def trigger_auto(self):
        self.scope.write(":TRIG:SWE AUTO")

    def trigger_force(self):
        self.scope.write(":TRIG:FORC")

    def trigger_normal(self):
        self.scope.write(":TRIG:SWE NORM")

    def is_running(self) -> bool:
        try:
            cond = int(self.scope.query(":OPER:COND?"))
            return bool(cond & 0b1000)      # Bit 3
        except Exception as e:
            self.log(f"Runstate error: {e}")
            return self.running

    # ---------- Screenshot / Setup ----------

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
        self.scope.write(f":DISPlay:DATA? PNG,{palette}")
        raw = self.scope.read_raw()

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

    def get_setup(self) -> bytes:
        # --- Binary mode ---
        self.scope.write_termination = ''
        self.scope.read_termination = ''
        old_timeout = self.scope.timeout
        self.scope.timeout = 5000

        # --- Request setup ---
        self.scope.write(":SYSTem:SETup?")
        raw = self.scope.read_raw()

        # --- Restore ASCII mode ---
        self.scope.write_termination = '\n'
        self.scope.read_termination = '\n'
        self.scope.timeout = old_timeout

        # --- Strip IEEE-488.2 binary header ---
        if raw.startswith(b"#"):
            n = int(raw[1:2])
            length = int(raw[2:2 + n])
            data = raw[2 + n:2 + n + length]
        else:
            data = raw

        return data

    def write_setup_data(self, data: bytes) -> bool:
        try:
            # Binary Setup wiederherstellen
            header = f"#{len(str(len(data)))}{len(data)}".encode()
            payload = header + data

            self.scope.write_termination = ''
            self.scope.read_termination = ''
            self.scope.write_raw(b":SYSTem:SETup " + payload)
            self.scope.flush(pyvisa.constants.VI_WRITE_BUF)

            self.scope.write_termination = '\n'
            self.scope.read_termination = '\n'

            return True

        except Exception:
            return False