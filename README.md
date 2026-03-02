# Scope Footswitch Trigger
Scope Footswitch Trigger enables hands-free control of a Keysight oscilloscope using a dual footswitch connected through an Arduino Nano.

The Arduino detects short and long presses on two foot pedals and sends events via USB (Serial) to a PC. A Python application running in the background receives these events and remotely controls the oscilloscope over LAN using SCPI commands.

This setup is ideal for lab environments where both hands are occupied — for example during probing, debugging hardware, or EMC measurements.

## Usage
<p align="center">
  <img src="doc/device_overview.png" width="80%" title="Device overview"  alt="accessibility text">
</p>

- Connect the dual footswitch to the PC via USB.
- Connect the oscilloscope to the network and optain its IP address via Utility → I/O on the oscilloscope.
- Start `OsciFootswitch.exe` (or `python OsciFootswitch.py`).
- Enter the oscilloscope’s IP address and click **\<Connect\>**.
- Use the "Identify Oscilloscope" checkbox to display a text box on the oscilloscope screen to verify the correct device.
- Select the correct serial port of the footswitch (identifier "USB-Serial CH340") and click **\<Open\>**.

→ The footswitch is ready.

## 🔧 System Overview

### Hardware
- Dual footswitch
- Arduino Nano
- USB connection to PC
- Oscilloscope (Keysight/Agilent with LAN & SCPI support)

### Software
- Arduino firmware (button press detection: short / long press)
- Python application (Serial + LAN/SCPI control)

## 🎯 Features
- Detects short and long presses for both pedals
- Remote oscilloscope control via LAN
- Trigger control:
  - RUN / START
  - STOP
  - SINGLE (Single Shot)
- Toggle between:
  - Normal Trigger Mode
  - Auto Trigger Mode
- Capture and store:
  - Screenshot
  - Full oscilloscope setup

## ⚙️ How It Works
1. The Arduino monitors two input pins connected to a dual footswitch.
2. Short and long presses are detected directly on the Arduino.
3. Events are sent via USB Serial (e.g. B1S, B1L, B2S, B2L).
4. The Python application:
  - Opens the configured serial port
  - Connects to the oscilloscope via IP (LAN)
  - Maps footswitch events to SCPI commands
5. The oscilloscope executes the corresponding trigger or screenshot command.

## 🧪 Example Use Cases
- Trigger single acquisition while holding probes
- Quickly toggle between Auto and Normal trigger during debugging
- Capture a screenshot including instrument setup without touching the scope
- Improve workflow in production test environments

## 🚀 Advantages
- Hands-free operation
- Minimal hardware cost
- Works in background
- No modification of oscillososcope required
- Fully scriptable and extendable


## Alternatively via Python Script

The program starts significantly faster when run via the Python script.
However, the required libraries must be installed first:

```bash
pip install pyinstaller pyvisa pyserial PySide6
```

→ Start the program with:

```bash
python OsciFootswitch.py
```

For example, via `OsciFootswitch.bat`.

## Generating the EXE from the Python Script

* Install the required libraries:

```bash
pip install pyinstaller pyvisa pyserial PySide6
```

Used package versions:

```text
pyinstaller==6.16.0
pyinstaller-hooks-contrib==2025.9
PyVISA==1.16.0
PyVISA-py==0.8.1
pyserial==3.5
PySide6==6.10.1
PySide6_Addons==6.10.1
PySide6_Essentials==6.10.1
```

* Build the EXE:

```bash
pyinstaller --onefile --windowed --hidden-import=pyvisa_py .\OsciFootswitch.py
```

→ The EXE will be available at:

```text
.\dist\OsciFootswitch.exe
```

