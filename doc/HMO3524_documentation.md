# HMO3524

## Overview
The available **HMO3524 oscilloscope** is an early hardware/firmware revision.  
Support from Hameg respectively Rhode & Schwarz for this version is very limited.

Older firmware versions and corresponding documentation are:
- difficult to find  
- often not publicly available  

As a result, reverse engineering and testing were required to evaluate SCPI support.

---

## SCPI Investigation

A custom script (`hameScpiChecker.py`) was used to:

- test known SCPI commands  
- probe undocumented commands  
- identify supported vs. unsupported functionality  

### Findings

- Only a **very limited subset of SCPI commands** is supported  
- Many standard commands (e.g. `RUN`, `STOP`, `SINGLE`) are:
  - not implemented, or  
  - ignored without proper error reporting  

- Some commands (e.g. `ACQ:TYPE`, partial `TRIG` queries) work inconsistently  

---

## Connectivity

Unlike most modern oscilloscopes, this device:

- ❌ does **not support standard VISA INSTR connections**
- ✅ is only accessible via **raw TCP socket**: `TCPIP::<IP>::50000::SOCKET`


This also leads to:

- unreliable SCPI responses  
- inconsistent error handling (`SYST:ERR?`)  
- missing or partial query replies  

---

## Conclusion

Due to the limitations:

- missing essential SCPI commands (RUN/STOP/SINGLE)  
- unreliable communication over TCP socket  
- incomplete firmware implementation  

👉 **This oscilloscope is not supported by this project.**

---

## Device Information

| Parameter          | Value        |
|-------------------|-------------|
| Device Class      | Oscilloscope |
| Device Type       | HMO3524      |
| Firmware Version  | 01.020       |
| Interface Type    | HO730        |
| HW Version        | 1.001        |
| SW Version        | 2.000        |

---

## Test Script

Script used for testing:
[```hamegScpiChecker.py```](hamegScpiChecker.py)


---

## Script Output

```text
>>> CLEAR ERRORS (*CLS)

============================================================
IDENTIFICATION
============================================================

>>> QUERY: *IDN?
<<< RESPONSE: HAMEG,HMO3524,056270075,HW10110000,SW01.020
>>> QUERY: SYST:ERR:ALL?
<<< ERRORS: 0,"No error"

============================================================
TRIGGER
============================================================

>>> WRITE: TRIG:A:MODE AUTO
>>> QUERY: SYST:ERR:ALL?
<<< ERRORS: 0,"No error"

>>> QUERY: TRIG:A:MODE?
<<< RESPONSE: AUTO
>>> QUERY: SYST:ERR:ALL?
<<< ERRORS: 0,"No error"

>>> WRITE: TRIG:A:MODE NORM
>>> QUERY: SYST:ERR:ALL?
ERR QUERY FAILED: VI_ERROR_TMO (-1073807339): Timeout expired before operation completed.

>>> QUERY: TRIG:A:MODE?
<<< RESPONSE: AUTO
>>> QUERY: SYST:ERR:ALL?
<<< ERRORS: -221,"Settings conflict",-101,"Invalid character",-101,"Invalid character",-101,"Invalid character",-113,"Undefined header"

============================================================
ACQ TYPE (WORKING)
============================================================

>>> QUERY: ACQ:TYPE?
<<< RESPONSE: ROLL
>>> QUERY: SYST:ERR:ALL?
<<< ERRORS: 0,"No error"

>>> WRITE: ACQ:TYPE ROLL
>>> QUERY: SYST:ERR:ALL?
<<< ERRORS: 0,"No error"

>>> QUERY: ACQ:TYPE?
<<< RESPONSE: ROLL
>>> QUERY: SYST:ERR:ALL?
<<< ERRORS: 0,"No error"

>>> WRITE: ACQ:TYPE REFresh
>>> QUERY: SYST:ERR:ALL?
<<< ERRORS: 0,"No error"

>>> QUERY: ACQ:TYPE?
<<< RESPONSE: REFR
>>> QUERY: SYST:ERR:ALL?
<<< ERRORS: 0,"No error"

============================================================
ACQ STATE (SHOULD WORK)
============================================================

>>> QUERY: ACQ:STATE?
QUERY ERROR: VI_ERROR_TMO (-1073807339): Timeout expired before operation completed.
>>> QUERY: SYST:ERR:ALL?
<<< ERRORS: -101,"Invalid character"

>>> WRITE: ACQ:STATE RUN
>>> QUERY: SYST:ERR:ALL?
<<< ERRORS: -101,"Invalid character"

>>> WRITE: ACQ:STATE STOP
>>> QUERY: SYST:ERR:ALL?
<<< ERRORS: -101,"Invalid character"

============================================================
RUN / STOP (CLASSIC)
============================================================

>>> WRITE: RUN
>>> QUERY: SYST:ERR:ALL?
<<< ERRORS: -101,"Invalid character"

>>> WRITE: STOP
>>> QUERY: SYST:ERR:ALL?
<<< ERRORS: -101,"Invalid character",-101,"Invalid character"

>>> WRITE: RUNSingle
>>> QUERY: SYST:ERR:ALL?
<<< ERRORS: -101,"Invalid character"

>>> WRITE: RUNSINGLE
>>> QUERY: SYST:ERR:ALL?
<<< ERRORS: -101,"Invalid character"

>>> WRITE: SINGLE
>>> QUERY: SYST:ERR:ALL?
<<< ERRORS: -101,"Invalid character",-101,"Invalid character"

>>> WRITE: SINGle
>>> QUERY: SYST:ERR:ALL?
<<< ERRORS: -101,"Invalid character",-101,"Invalid character"

============================================================
SINGLE / STOPAFTER
============================================================

>>> WRITE: ACQ:A:STOPAFTER SEQ
>>> QUERY: SYST:ERR:ALL?
<<< ERRORS: -113,"Undefined header",-101,"Invalid character"

>>> WRITE: ACQ:A:STATE RUN
>>> QUERY: SYST:ERR:ALL?
<<< ERRORS: -113,"Undefined header",-101,"Invalid character"

============================================================
SCREENSHOT
============================================================

>>> QUERY: HCOPy:DATA?
QUERY ERROR: 'ascii' codec can't decode byte 0x80 in position 26: ordinal not in range(128)
>>> QUERY: SYST:ERR:ALL?
<<< ERRORS: 0,"No error"

============================================================
OVERVIEWS of different parts
============================================================

>>> QUERY: ACQ?
<<< RESPONSE: :ACQ:TYPE REFR;:ACQ:AVER:COUN 2.0E+00;:ACQ:REAL ON;:ACQ:PEAK OFF;:ACQ:HRES OFF;:ACQ:WRAT AUTO
>>> QUERY: SYST:ERR:ALL?
<<< ERRORS: 0,"No error"

>>> QUERY: TRIG?
<<< RESPONSE: :TRIG:A:MODE NORM;:TRIG:A:TYPE EDGE;:TRIG:A:EDGE:SOUR CH1;:TRIG:A:EDGE:SLOP POS;:TRIG:A:EDGE:COUP DC;:TRIG:A:EDGE:LEV 0.0E+00;:TRIG:A:EDGE:FILT:LPAS OFF;:TRIG:A:EDGE:FILT:NREJ ON;:TRIG:A:VID:FIEL ALL;:TRIG:A:VID:LINE 0.0E+00;:TRIG:A:VID:POL POS;:TRIG:A:VID:STAN PAL;:TRIG:A:VID:SOUR CH1;:TRIG:B:STAT OFF;:TRIG:B:LEV 0.0E+00
>>> QUERY: SYST:ERR:ALL?
<<< ERRORS: 0,"No error"

>>> QUERY: HCOP?
<<< RESPONSE: :HCOP:FORM BMP;:HCOP:SIZE:X 640;:HCOP:SIZE:Y 520
>>> QUERY: SYST:ERR:ALL?
<<< ERRORS: 0,"No error"

>>> QUERY: SYST?
<<< RESPONSE: :SYST:NAME ""
>>> QUERY: SYST:ERR:ALL?
<<< ERRORS: 

DONE.
```
