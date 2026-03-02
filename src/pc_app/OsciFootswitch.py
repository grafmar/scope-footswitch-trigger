import sys
import threading
import queue

import serial
import serial.tools.list_ports
import pyvisa

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QComboBox, QLineEdit, QCheckBox, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QSizePolicy
)

from PySide6.QtCore import Qt, QTimer, QByteArray
from PySide6.QtGui import QPixmap

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

# ----------------------------
# Oscilloscope Controller
# ----------------------------
class ScopeController:
    def __init__(self, log_callback=None):
        self.rm = pyvisa.ResourceManager("@py")
        self.scope = None
        self.running = False
        self.log = log_callback or (lambda msg: None)

    def connect(self, ip):
        self.scope = self.rm.open_resource(f"TCPIP0::{ip}::INSTR")
        self.scope.timeout = 5000
        return self.scope.query("*IDN?")

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
        self.scope.write(":TRIG:MODE AUTO")

    def trigger_normal(self):
        self.scope.write(":TRIG:MODE NORM")

    # ---------- Screenshot / Setup ----------

    def get_screenshot_png(self, color: bool, inverted: bool) -> bytes:
        """
        color: True  -> COLor
            False -> GRAYscale
        inverted: True / False -> HARDcopy:INKSaver
        """

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
        self.scope.write(f":DISPlay:DATA? PNG,SCReen,{palette}")
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

        # --- Oscilloscope config ---
        osc_layout = QHBoxLayout()
        osc_layout.addWidget(QLabel("Scope IP:"))
        self.ip_edit = QLineEdit("10.53.48.103")
        osc_layout.addWidget(self.ip_edit)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.connect_scope)
        osc_layout.addWidget(self.connect_btn)

        layout.addLayout(osc_layout)

        self.identify_cb = QCheckBox("Identify Oscilloscope")
        self.identify_cb.toggled.connect(self.identify_scope)
        layout.addWidget(self.identify_cb)

        # --- Serial config ---
        ser_layout = QHBoxLayout()
        ser_layout.addWidget(QLabel("Serial Port:"))
        self.serial_combo = SerialPortComboBox(self.refresh_serial_ports)
        ser_layout.addWidget(self.serial_combo)

        self.open_serial_btn = QPushButton("Open")
        self.open_serial_btn.clicked.connect(self.open_serial)
        ser_layout.addWidget(self.open_serial_btn)

        layout.addLayout(ser_layout)

        # --- Footswitch Table ---
        self.table = QTableWidget(2, 2)
        self.table.setHorizontalHeaderLabels(["B1 (Left)", "B2 (Right)"])
        self.table.setVerticalHeaderLabels(["Short", "Long"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)

        self.table.setItem(0, 0, QTableWidgetItem("RUN ↔ STOP"))
        self.table.setItem(0, 1, QTableWidgetItem("TRIGGER NORMAL, SINGLE"))
        self.table.setItem(1, 0, QTableWidgetItem("TRIGGER AUTO, RUN"))
        self.table.setItem(1, 1, QTableWidgetItem("TRIGGER AUTO, SINGLE"))

        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        layout.addWidget(self.table)

        # Tabelle fixieren (keine vertikale Skalierung)
        self.table.setFixedHeight(80)  # passt für 2 Zeilen
        self.table.setFixedWidth(400)
        self.table.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # --- Screenshot Controls ---
        shot_layout = QHBoxLayout()

        # Preview Screenshot
        self.preview_btn = QPushButton("Preview")
        self.preview_btn.clicked.connect(self.preview_screenshot)
        self.preview_btn.setMinimumHeight(50)  # doppelte Höhe
        self.preview_btn.setStyleSheet("font-size: 14pt; font-weight: bold;")
        shot_layout.addWidget(self.preview_btn)

        # Save PNG + Setup
        self.save_btn = QPushButton("Save PNG + Setup")
        self.save_btn.clicked.connect(self.save_screenshot_and_setup)
        self.save_btn.setMinimumHeight(50)
        self.save_btn.setStyleSheet("font-size: 14pt; font-weight: bold;")
        shot_layout.addWidget(self.save_btn)

        # Load Setup
        self.load_setup_btn = QPushButton("Load Setup")
        self.load_setup_btn.clicked.connect(self.load_setup)
        self.load_setup_btn.setMinimumHeight(50)
        self.load_setup_btn.setStyleSheet("font-size: 14pt; font-weight: bold;")
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

        layout.addLayout(shot_layout)

        # --- Preview Label ---
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(768, 622)  # 4:3 Verhältnis, größer in Y
        self.image_label.setStyleSheet("border: 1px solid gray; background-color: gray;")
        layout.addWidget(self.image_label)

        # --- Log ---
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedHeight(6 * 20)  # 6 Zeilen à ca. 20px pro Zeile
        self.log.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
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
        try:
            with open(filename, "rb") as f:
                data = f.read()

            # Binary Setup wiederherstellen
            header = f"#{len(str(len(data)))}{len(data)}".encode()
            payload = header + data

            self.scope.write_termination = ''
            self.scope.read_termination = ''
            self.scope.write_raw(":SYSTem:SETup ", payload)
            self.scope.write_termination = '\n'
            self.scope.read_termination = '\n'

            self.log_msg(f"Setup loaded: {filename}")

        except Exception as e:
            self.log_msg(f"Failed to load setup: {e}")

    # ---------- Event Handling ----------

    def process_events(self):
        while not self.event_queue.empty():
            self.handle_event(self.event_queue.get())

    def handle_event(self, event):
        try:
            if event == "B1S":
                if self.scope.running:
                    self.scope.stop()
                    self.log_msg(f"Event {event}: STOP")
                else:
                    self.scope.run()
                    self.log_msg(f"Event {event}: RUN")

            elif event == "B1L":
                self.scope.trigger_auto()
                self.scope.run()
                self.log_msg(f"Event {event}: TRIGGER AUTO, RUN")

            elif event == "B2S":
                self.scope.trigger_normal()
                self.scope.single()
                self.log_msg(f"Event {event}: TRIGGER NORMAL, SINGLE")

            elif event == "B2L":
                self.scope.trigger_auto()
                self.scope.single()
                self.log_msg(f"Event {event}: TRIGGER AUTO, SINGLE")

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
    win.resize(800, 650)
    win.show()
    sys.exit(app.exec())
