import sys
import threading
import queue
import time

import serial
import serial.tools.list_ports
import pyvisa

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QComboBox, QLineEdit, QCheckBox, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView
)

from PySide6.QtCore import Qt, QTimer

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
            # self.log("OSC -> IDENTIFY ON")
        else:
            self.scope.write(':SYST:DSP ""')
            # self.log("OSC -> IDENTIFY OFF")

    def run(self):
        self.scope.write(":RUN")
        # self.log("OSC -> RUN")
        self.running = True

    def stop(self):
        self.scope.write(":STOP")
        # self.log("OSC -> STOP")
        self.running = False

    def single(self):
        self.scope.write(":SINGLE")
        # self.log("OSC -> SINGLE")

    def trigger_auto(self):
        self.scope.write(":TRIG:MODE AUTO")
        # self.log("OSC -> TRIG:MODE AUTO")

    def trigger_normal(self):
        self.scope.write(":TRIG:MODE NORM")
        # self.log("OSC -> TRIG:MODE NORM")

    def force_trigger(self):
        # self.scope.write(":TRIG:FORC")
        self.scope.write("*TRG")
        # self.log("OSC -> TRIG:FORC")

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

        self.idn_label = QLabel("IDN: not connected")
        layout.addWidget(self.idn_label)

        self.identify_cb = QCheckBox("Identify Oscilloscope")
        self.identify_cb.toggled.connect(self.identify_scope)
        layout.addWidget(self.identify_cb)

        # --- Serial config ---
        ser_layout = QHBoxLayout()
        ser_layout.addWidget(QLabel("Serial Port:"))
        # self.serial_combo = QComboBox()
        self.serial_combo = SerialPortComboBox(self.refresh_serial_ports)
        ser_layout.addWidget(self.serial_combo)

        self.open_serial_btn = QPushButton("Open")
        self.open_serial_btn.clicked.connect(self.open_serial)
        ser_layout.addWidget(self.open_serial_btn)

        layout.addLayout(ser_layout)

        # --- Footswitch Table ---
        self.table = QTableWidget(2, 2)  # 2 Zeilen, 2 Spalten
        self.table.setHorizontalHeaderLabels(["B1 (Left)", "B2 (Right)"])
        self.table.setVerticalHeaderLabels(["Short", "Long"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # Nur Anzeige
        self.table.setFixedHeight(80)  # optional: Höhe anpassen
        self.table.setFixedWidth(400)  # optional

        # Werte eintragen
        self.table.setItem(0, 0, QTableWidgetItem("RUN ↔ STOP"))              # B1S
        self.table.setItem(0, 1, QTableWidgetItem("TRIGGER NORMAL, SINGLE"))  # B2S
        self.table.setItem(1, 0, QTableWidgetItem("TRIGGER AUTO, RUN"))       # B1L
        self.table.setItem(1, 1, QTableWidgetItem("TRIGGER AUTO, SINGLE"))    # B2L

        layout.addWidget(self.table)

        # --- Tabelle stylen ---
        # Nicht selektierbar
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)

        # Spaltenbreite automatisch an Text anpassen
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.verticalHeader().setDefaultSectionSize(30)

        # Schriftgröße
        self.table.setStyleSheet("QTableWidget { font-size: 12pt; }")

        # --- Log ---
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        self.setLayout(layout)

    def refresh_serial_ports(self):
        self.serial_combo.clear()
        for port in serial.tools.list_ports.comports():
            text = f"{port.device} - {port.description}"
            self.serial_combo.addItem(text, port.device)

    def connect_scope(self):
        try:
            idn = self.scope.connect(self.ip_edit.text())
            self.idn_label.setText(f"IDN: {idn.strip()}")
            self.log_msg(f"Connected to scope: {idn.strip()}")
        except Exception as e:
            self.log_msg(str(e))

    def identify_scope(self, checked: bool):
        try:
            self.scope.identify(checked)
            self.log_msg(f"OSC -> Identify {checked}")
        except Exception as e:
            self.log_msg(str(e))

    def open_serial(self):
        port = self.serial_combo.currentData()
        self.serial_thread = SerialReader(port, 115200, self.event_queue)
        self.serial_thread.start()
        self.log_msg(f"Opened serial {port}")

    def process_events(self):
        while not self.event_queue.empty():
            event = self.event_queue.get()
            # self.log_msg(f"Event: {event}")
            self.handle_event(event)

    def handle_event(self, event):
        # Expected events: B1S, B1L, B2S, B2L
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
                self.log_msg(f"Event {event}: TRIGGER AUTO, SINGLE (FORCE TRIGGER)")

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
    win.resize(600, 400)
    win.show()
    sys.exit(app.exec())
