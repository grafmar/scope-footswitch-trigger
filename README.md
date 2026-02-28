# Scope Footswitch Trigger
Scope Footswitch Trigger enables hands-free control of a Keysight oscilloscope using a dual footswitch connected through an Arduino Nano.

The Arduino detects short and long presses on two foot pedals and sends events via USB (Serial) to a PC. A Python application running in the background receives these events and remotely controls the oscilloscope over LAN using SCPI commands.

This setup is ideal for lab environments where both hands are occupied — for example during probing, debugging hardware, or EMC measurements.

## Usage
<p align="center">
  <img src="doc/device_overview.png" width="80%" title="Device overview"  alt="accessibility text">
</p>

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
