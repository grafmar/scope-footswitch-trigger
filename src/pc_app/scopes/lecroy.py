from .base import BaseScope
from PIL import Image
import io


# ----------------------------
# LeCroy Scope
# ----------------------------
class LeCroyScope(BaseScope):

    def identify(self, enable: bool):
        if enable:
            self.scope.write('MESSAGE "FOOT SWITCH IDENTIFIER"')
        else:
            self.scope.write('MESSAGE ""')

    def run(self):
        self.scope.write("TRIG_MODE NORM")
        self.running = True

    def stop(self):
        self.scope.write("TRIG_MODE STOP")
        self.running = False

    def single(self):
        self.scope.write("TRIG_MODE SINGLE")

    def trigger_auto(self):
        self.scope.write("TRIG_MODE AUTO")

    def trigger_force(self):
        self.scope.write("TRIG_MODE AUTO")
        self.scope.write("WAIT")
        self.scope.write("TRIG_MODE STOP")

    def trigger_normal(self):
        self.scope.write("TRIG_MODE NORM")

    def get_screenshot_png(self, color: bool, inverted: bool) -> bytes:
        bckg = "WHITE" if inverted else "BLACK"

        # configure hardcopy for screenshot (TIFF, GPIB port, background color)
        self.scope.write(f"HCSU DEV,TIFF,PORT,GPIB,BCKG,{bckg}")

        # trigger screenshot
        self.scope.write("SCDP")

        # read binary data
        data = self.scope.read_raw()

        # convert TIFF -> PNG
        image = Image.open(io.BytesIO(data))
        png_buffer = io.BytesIO()
        image.save(png_buffer, format="PNG")

        return png_buffer.getvalue()

    def save_setup(self, filename: str):

        # --- Binary mode ---
        self.scope.write_termination = ''
        self.scope.read_termination = ''
        old_timeout = self.scope.timeout
        self.scope.timeout = 5000

        # --- Request setup ---
        self.scope.write("PNSU?") # SAVE/RECALL SETUP PANEL_SETUP, PNSU
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
            self.scope.write_raw(b"PNSU " + payload)
            self.scope.write_termination = '\n'
            self.scope.read_termination = '\n'

            return True

        except Exception:
            return False
