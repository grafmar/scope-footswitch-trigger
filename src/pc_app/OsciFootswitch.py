import sys
import threading
import queue

import serial
import serial.tools.list_ports
import pyvisa

from PySide6.QtWidgets import (
    QApplication, QLayout, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QComboBox, QLineEdit, QCheckBox, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QSizePolicy, QGridLayout, QFrame
)

from PySide6.QtCore import Qt, QTimer, QByteArray
from PySide6.QtGui import QPixmap, QFont

from PIL import Image
import io

# ----------------------------
# Serial Reader Thread
# ----------------------------
class SerialReader(threading.Thread):
    def __init__(self, port, baudrate, event_queue):
        super().__init__(daemon=True)
        self.port = port
        self.baudrate = baudrate
        self.queue = event_queue
        self._running = True
        self.ser = None

    def run(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            while self._running:
                line = self.ser.readline().decode(errors="ignore").strip()
                if line:
                    self.queue.put(line)
        except Exception as e:
            self.queue.put(f"ERROR:{e}")

    def stop(self):
        self._running = False
        if self.ser:
            self.ser.close()


# ============================================================
# Oscilloscope Implementations
# ============================================================

# ----------------------------
# Base Scope
# ----------------------------
class BaseScope:

    def __init__(self, scope, log):
        self.scope = scope
        self.log = log
        self.running = False

    def identify(self, enable: bool):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def single(self):
        raise NotImplementedError

    def trigger_auto(self):
        raise NotImplementedError

    def trigger_force(self):
        raise NotImplementedError

    def trigger_normal(self):
        raise NotImplementedError

    def is_running(self) -> bool:
        return self.running

    def get_screenshot_png(self, color: bool, inverted: bool) -> bytes:
        raise NotImplementedError

    def save_setup(self, filename: str):
        raise NotImplementedError

    def write_setup(self, filename: str) -> bool:
        raise NotImplementedError


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

    def save_setup(self, filename: str):

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
            self.scope.write_raw(b":SYSTem:SETup " + payload)
            self.scope.write_termination = '\n'
            self.scope.read_termination = '\n'

            return True

        except Exception:
            return False


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
        self.scope.write("TRIG_MODE AUTO")
        self.running = True

    def stop(self):
        # ACQUISITION STOP
        # ACQUISITION TRIG_MODE, TRMD
        # <mode> : = { AUTO, NORM, SINGLE, STOP}
        self.scope.write("TRIG_MODE STOP")
        self.running = False

    def single(self):
        # ARM
        # ACQUISITION ARM_ACQUISITION, ARM
        self.scope.write("TRIG_MODE SINGLE")

    def trigger_auto(self):
        self.scope.write("TRIG_MODE AUTO")

    def trigger_force(self):
        self.scope.write("FORCE_TRIGGER")

    def trigger_normal(self):
        self.scope.write("TRIG_MODE NORM")

    def get_screenshot_png(self, color: bool, inverted: bool) -> bytes:

        # ---------- Binary mode ----------
        self.scope.write_termination = ''
        self.scope.read_termination = ''
        old_timeout = self.scope.timeout
        self.scope.timeout = 10000

        self.scope.write("HARDCOPY_SETUP DEV,PNG")  # HCSU HARDCOPY_SETUP
        self.scope.write("SCREEN_DUMP")             # SCDP SCREEN_DUMP
        raw = self.scope.read_raw()

        # ---------- Restore ASCII mode ----------
        self.scope.write_termination = '\n'
        self.scope.read_termination = '\n'
        self.scope.timeout = old_timeout

        if raw.startswith(b"#"):
            n = int(raw[1:2])
            length = int(raw[2:2 + n])
            data = raw[2 + n:2 + n + length]
        else:
            data = raw

        return data

    def save_setup(self, filename: str):
        # SAVE/RECALL SETUP PANEL_SETUP, PNSU
        self.scope.write(f"STORE_PANEL '{filename}'")

    def write_setup(self, filename: str) -> bool:
        try:
            self.scope.write(f"RECALL_PANEL '{filename}'")
            return True
        except Exception:
            return False


# ============================================================
# Scope Controller (Factory + Delegation)
# ============================================================

class ScopeController:
    def __init__(self, log_callback=None):
        self.rm = pyvisa.ResourceManager("@py")
        self.scope = None
        self.device: BaseScope | None = None
        self.log = log_callback or (lambda msg: None)

    def connect(self, ip):

        self.scope = self.rm.open_resource(f"TCPIP0::{ip}::INSTR")
        self.scope.timeout = 5000

        idn = self.scope.query("*IDN?")
        idn_u = idn.upper()

        if "LECROY" in idn_u:
            self.device = LeCroyScope(self.scope, self.log)
            self.log("Detected LeCroy oscilloscope")

        elif "KEYSIGHT" in idn_u or "AGILENT" in idn_u:
            self.device = KeysightScope(self.scope, self.log)
            self.log("Detected Keysight/Agilent oscilloscope")

        else:
            self.device = KeysightScope(self.scope, self.log)
            self.log("Unknows oscilloscope. Using Keysight/Agilent commands as default.")

        return idn

    # ---------- Delegation ----------

    def identify(self, enable):
        self.device.identify(enable)

    def run(self):
        self.device.run()

    def stop(self):
        self.device.stop()

    def single(self):
        self.device.single()

    def trigger_auto(self):
        self.device.trigger_auto()

    def trigger_force(self):
        self.device.trigger_force()

    def trigger_normal(self):
        self.device.trigger_normal()

    def is_running(self):
        return self.device.is_running()

    def get_screenshot_png(self, color, inverted):
        return self.device.get_screenshot_png(color, inverted)

    def save_setup(self, filename):
        self.device.save_setup(filename)

    def write_setup(self, filename):
        return self.device.write_setup(filename)

# ----------------------------
# Serial ports dropdown
# ----------------------------
class SerialPortComboBox(QComboBox):
    def __init__(self, refresh_callback, parent=None):
        super().__init__(parent)
        self.refresh_callback = refresh_callback

    def showPopup(self):
        self.refresh_callback()
        super().showPopup()


# ----------------------------
# Main GUI
# ----------------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Footswitch Oscilloscope Controller")

        self.event_queue = queue.Queue()
        self.serial_thread = None
        self.scope = ScopeController(self.log_msg)

        self.init_ui()
        self.refresh_serial_ports()

        self.timer = QTimer()
        self.timer.timeout.connect(self.process_events)
        self.timer.start(100)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setHorizontalSizeConstraint(QLayout.SetMinimumSize)

        config_layout = QGridLayout()
        config_layout.setHorizontalSpacing(10)
        config_layout.setVerticalSpacing(10)

        # ---- Labels (gleich breit) ----
        label_width = 100

        scope_label = QLabel("Scope IP:")
        scope_label.setFixedWidth(label_width)

        serial_label = QLabel("Footswitch Port:")  # besser als "Serial Port"
        serial_label.setFixedWidth(label_width)

        # ---- Scope Row ----
        self.ip_edit = QLineEdit("10.53.48.103")
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.connect_scope)

        self.identify_cb = QCheckBox("Identify")
        self.identify_cb.toggled.connect(self.identify_scope)

        # ---- Serial Row ----
        self.serial_combo = SerialPortComboBox(self.refresh_serial_ports)
        self.open_serial_btn = QPushButton("Open")
        self.open_serial_btn.clicked.connect(self.open_serial)

        # ---- Buttons gleich breit ----
        button_width = 100
        self.connect_btn.setFixedWidth(button_width)
        self.open_serial_btn.setFixedWidth(button_width)

        # ---- Inputs gleich breit ----
        input_width = 220
        self.ip_edit.setFixedWidth(input_width)
        self.serial_combo.setFixedWidth(input_width)

        # ---- Grid anordnen ----
        config_layout.addWidget(scope_label,        0, 0)
        config_layout.addWidget(self.ip_edit,       0, 1)
        config_layout.addWidget(self.connect_btn,   0, 2)
        config_layout.addWidget(self.identify_cb,   0, 3)

        config_layout.addWidget(serial_label,       1, 0)
        config_layout.addWidget(self.serial_combo,  1, 1)
        config_layout.addWidget(self.open_serial_btn, 1, 2)

        layout.addLayout(config_layout)

        # ---- Separator ----
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setMaximumWidth(768)
        layout.addWidget(separator)

        # --- Footswitch Table ---
        layout.addWidget(QLabel("Footswitch Functions:"))
        self.table = QTableWidget(2, 3)
        self.table.setHorizontalHeaderLabels(["B1 (Left)", "B1+B2 (Both)", "B2 (Right)"])
        self.table.setVerticalHeaderLabels(["Short", "Long"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)

        # -------- Layout behaviour --------
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)  # alle Spalten gleich breit
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("""
        /* Tabelle */
        QTableWidget {
            background-color: #f0f0f0;        /* same color as  GUI */
            gridline-color: #707070;          /* darker Gridlines */
            border: 1px solid #707070;
        }

        /* Horizontal + Vertical Header */
        QHeaderView::section {
            background-color: #c8c8c8;        /* Header gray */
            color: black;
            font-weight: bold;
            border: 0px solid #707070;        /* darker lines also here */
            border-right: 1px solid #707070;
            border-bottom: 1px solid #707070;
        }

        /* Top-Left Corner */
        QTableCornerButton::section {
            background-color: #f0f0f0;        /* same color as Header */
            border: 0px solid #707070;        /* darker lines also here */
        }
        """)

        # -------- Schrift fett --------
        bold_font = QFont()
        bold_font.setBold(True)

        def set_item(row, col, text):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignCenter)  # zentriert
            item.setFont(bold_font)                # fett
            self.table.setItem(row, col, item)

        set_item(0, 0, "RUN ↔ STOP")
        set_item(0, 1, "Preview")
        set_item(0, 2, "SINGLE, TRIGGER NORMAL")
        set_item(1, 0, "RUN, TRIGGER AUTO")
        set_item(1, 1, "Save PNG + Setup")
        set_item(1, 2, "SINGLE, FORCE TRIGGER")

        layout.addWidget(self.table)

        # Tabelle fixieren (keine vertikale Skalierung)
        self.table.setFixedHeight(80)  # passt für 2 Zeilen
        self.table.setFixedWidth(768)
        self.table.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # ---- Separator ----
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setMaximumWidth(768)
        layout.addWidget(separator)

        # --- Screenshot Controls ---
        shot_widget = QWidget()
        shot_widget.setFixedWidth(768)
        shot_layout = QHBoxLayout(shot_widget)

        # Preview Screenshot
        self.preview_btn = QPushButton("Preview")
        self.preview_btn.clicked.connect(self.preview_screenshot)
        self.preview_btn.setMinimumHeight(50)  # doppelte Höhe
        self.preview_btn.setStyleSheet("font-size: 14pt; font-weight: bold; padding: 5px 20px;")
        shot_layout.addWidget(self.preview_btn)

        # Save PNG + Setup
        self.save_btn = QPushButton("Save PNG + Setup")
        self.save_btn.clicked.connect(self.save_screenshot_and_setup)
        self.save_btn.setMinimumHeight(50)
        self.save_btn.setStyleSheet("font-size: 14pt; font-weight: bold; padding: 5px 20px;")
        shot_layout.addWidget(self.save_btn)

        # Load Setup
        self.load_setup_btn = QPushButton("Load Setup")
        self.load_setup_btn.clicked.connect(self.load_setup)
        self.load_setup_btn.setMinimumHeight(50)
        self.load_setup_btn.setStyleSheet("font-size: 14pt; font-weight: bold; padding: 5px 20px;")
        shot_layout.addWidget(self.load_setup_btn)

        # Spacer, damit rechts nichts wackelt
        shot_layout.addStretch()

        # --- Color / Invert Checkboxes rechts, enger zusammen ---
        cb_layout = QHBoxLayout()
        self.color_cb = QCheckBox("Color")
        self.color_cb.setChecked(True)
        cb_layout.addWidget(self.color_cb)

        self.invert_cb = QCheckBox("Inverted")
        cb_layout.addWidget(self.invert_cb)

        cb_layout.setSpacing(5)  # enger zusammen
        shot_layout.addLayout(cb_layout)

        layout.addWidget(shot_widget)

        # --- Preview Label ---
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(768, 576)  # 4:3 Verhältnis
        self.image_label.setStyleSheet("border: 1px solid gray; background-color: gray;")
        layout.addWidget(self.image_label)

        # --- Log ---
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedWidth(768)
        self.log.setMinimumHeight(6 * 20) # 6 Zeilen à ca. 20px pro Zeile
        self.log.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        layout.addWidget(self.log)

        self.setLayout(layout)

    # ---------- Helpers ----------

    def refresh_serial_ports(self):
        self.serial_combo.clear()
        for port in serial.tools.list_ports.comports():
            self.serial_combo.addItem(
                f"{port.device} - {port.description}", port.device
            )

    # ---------- Scope Actions ----------

    def connect_scope(self):
        try:
            idn = self.scope.connect(self.ip_edit.text())
            self.log_msg(f"Connected to scope: {idn.strip()}")
        except Exception as e:
            self.log_msg(str(e))

    def identify_scope(self, checked: bool):
        try:
            self.scope.identify(checked)
        except Exception as e:
            self.log_msg(str(e))

    def open_serial(self):
        port = self.serial_combo.currentData()
        self.serial_thread = SerialReader(port, 115200, self.event_queue)
        self.serial_thread.start()
        self.log_msg(f"Opened serial {port}")

    def closeEvent(self, event):
        if self.serial_thread:
            self.serial_thread.stop()
        event.accept()

    # ---------- Screenshot ----------

    def update_preview_from_png(self, data: bytes):
        pixmap = QPixmap()
        pixmap.loadFromData(data, "PNG")

        self.image_label.setPixmap(
            pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

    def preview_screenshot(self):
        try:
            data = self.scope.get_screenshot_png(
                color=self.color_cb.isChecked(),
                inverted=self.invert_cb.isChecked(),
            )

            self.update_preview_from_png(data)
            self.log_msg("Screenshot preview updated")

        except Exception as e:
            self.log_msg(str(e))

    def save_screenshot_and_setup(self):
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save Screenshot", "", "PNG Image (*.png)"
            )
            if not filename:
                return
            if not filename.lower().endswith(".png"):
                filename += ".png"

            # --- Screenshot EINMAL holen ---
            data = self.scope.get_screenshot_png(
                color=self.color_cb.isChecked(),
                inverted=self.invert_cb.isChecked(),
            )

            # --- Preview aktualisieren ---
            self.update_preview_from_png(data)

            # --- PNG speichern ---
            with open(filename, "wb") as f:
                f.write(data)

            # --- Setup speichern ---
            setup_file = filename.replace(".png", ".set")
            self.scope.save_setup(setup_file)

            self.log_msg(f"Saved screenshot and updated preview: {filename}")

        except Exception as e:
            self.log_msg(str(e))

    def load_setup(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Setup", "", "Setup Files (*.set *.bin)"
        )
        if not filename:
            return
        if self.scope.write_setup(filename):
            self.log_msg(f"Setup loaded back: {filename}")
        else:
            self.log_msg(f"Failed to load setup: {filename}")

    # ---------- Event Handling ----------

    def process_events(self):
        while not self.event_queue.empty():
            self.handle_event(self.event_queue.get())

    def handle_event(self, event):
        try:
            if event == "B1S":
                if self.scope.is_running():
                    self.scope.stop()
                    self.log_msg(f"Event {event}: STOP")
                else:
                    self.scope.run()
                    self.log_msg(f"Event {event}: RUN")

            elif event == "B1L":
                self.scope.run()
                self.scope.trigger_auto()
                self.log_msg(f"Event {event}: RUN, TRIGGER AUTO")

            elif event == "B2S":
                self.scope.trigger_normal()
                self.scope.single()
                self.log_msg(f"Event {event}: SINGLE, TRIGGER NORMAL")

            elif event == "B2L":
                self.scope.single()
                self.scope.trigger_force()
                self.log_msg(f"Event {event}: SINGLE, TRIGGER FORCE")

            elif event == "BBS":
                self.preview_screenshot()
                self.log_msg(f"Event {event}: Preview")

            elif event == "BBL":
                self.save_screenshot_and_setup()
                self.log_msg(f"Event {event}: Save PNG + Setup")

        except Exception as e:
            self.log_msg(str(e))

    def log_msg(self, msg):
        self.log.append(msg)

# ----------------------------
# Main
# ----------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(700, 650)
    win.show()
    sys.exit(app.exec())
