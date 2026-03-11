from .base import BaseScope


# ----------------------------
# Hameg/ Rohde & Schwarz Scope
# ----------------------------
class HamegScope(BaseScope):

    def identify(self, enable: bool):
        if enable:
            self.scope.write('DISP:DIAL:MESS "FOOT SWITCH\nIDENTIFIER"')
        else:
            self.scope.write('DISP:DIAL:CLOS')

    def run(self):
        self.scope.write(":RUN")
        self.running = True

    def stop(self):
        self.scope.write(":STOP")
        self.running = False

    def single(self):
        self.scope.write(":SINGLE")

    def trigger_auto(self):
        self.scope.write(":TRIG:MODE AUTO")

    def trigger_force(self):
        self.scope.write("*TRG")

    def trigger_normal(self):
        self.scope.write(":TRIG:MODE NORM")

    def is_running(self) -> bool:
        try:
            state = self.scope.query(":ACQuire:STATe?")
            return  "RUN" in state
        except Exception as e:
            self.log(f"Runstate error: {e}")
            return self.running

    # ---------- Screenshot / Setup ----------

    def get_screenshot_png(self, color: bool, inverted: bool) -> bytes:

        colorScheme = "COLor" if color else "GRAYscale"
        if inverted:
            colorScheme = "INVerted"

        # ---------- Binary mode ----------
        self.scope.write_termination = ''
        self.scope.read_termination = ''
        old_timeout = self.scope.timeout
        self.scope.timeout = 10000

        # ---------- Color Scheme ----------
        self.scope.write(f"HCOPy:COLOR:SCHeme {colorScheme}")

        # ---------- Request screen dump ----------
        self.scope.write(f"HCOPy:LANGuage PNG")
        self.scope.write(f"HCOPy:DATA?")
        
        raw = self.scope.read_raw()

        # ---------- Restore ASCII mode ----------
        self.scope.write_termination = '\n'
        self.scope.read_termination = '\n'
        self.scope.timeout = old_timeout

        """
        # ---------- Strip IEEE-488.2 binary header ----------
         if raw.startswith(b"#"):
            n = int(raw[1:2])
            length = int(raw[2:2 + n])
            data = raw[2 + n:2 + n + length]
        else:
            data = raw
        """

        return data

    def save_setup(self, filename: str):

        # --- Binary mode ---
        self.scope.write_termination = ''
        self.scope.read_termination = ''
        old_timeout = self.scope.timeout
        self.scope.timeout = 5000

        # --- Request setup ---
        self.scope.write(":SYSTem:SET?")
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

        # --- Save as binary ---
        with open(filename, "wb") as f:
            f.write(data)

    def write_setup(self, filename: str) -> bool:
        try:
            with open(filename, "rb") as f:
                data = f.read()

            # Binary Setup wiederherstellen
            header = f"#{len(str(len(data)))}{len(data)}".encode()
            payload = header + data

            self.scope.write_termination = ''
            self.scope.read_termination = ''
            self.scope.write_raw(b":SYSTem:SET " + payload)
            self.scope.write_termination = '\n'
            self.scope.read_termination = '\n'

            return True

        except Exception:
            return False
