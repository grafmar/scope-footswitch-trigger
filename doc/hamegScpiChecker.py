import pyvisa
import time

IP = "10.0.0.223"
PORT = 50000


# ----------------------------
# Connection
# ----------------------------
rm = pyvisa.ResourceManager("@py")
inst = rm.open_resource(f"TCPIP0::{IP}::{PORT}::SOCKET")

inst.read_termination = "\n"
inst.write_termination = "\n"
inst.timeout = 3000


# ----------------------------
# Helpers
# ----------------------------
def print_header(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def scpi_write(cmd):
    print(f"\n>>> WRITE: {cmd}")
    try:
        inst.write(cmd)
    except Exception as e:
        print(f"WRITE ERROR: {e}")
    time.sleep(0.2)
    scpi_err()


def scpi_query(cmd):
    print(f"\n>>> QUERY: {cmd}")
    try:
        resp = inst.query(cmd)
        print(f"<<< RESPONSE: {resp.strip()}")
    except Exception as e:
        print(f"QUERY ERROR: {e}")
    time.sleep(0.2)
    scpi_err()


def scpi_err():
    print(">>> QUERY: SYST:ERR:ALL?")
    try:
        err = inst.query("SYST:ERR:ALL?")
        print(f"<<< ERRORS: {err.strip()}")
    except Exception as e:
        print(f"ERR QUERY FAILED: {e}")


def clear_errors():
    print("\n>>> CLEAR ERRORS (*CLS)")
    try:
        inst.write("*CLS")
    except:
        pass
    time.sleep(0.2)


# ----------------------------
# Tests
# ----------------------------
def test_ident():
    print_header("IDENTIFICATION")
    scpi_query("*IDN?")


def test_trigger():
    print_header("TRIGGER")
    scpi_write("TRIG:A:MODE AUTO")
    scpi_query("TRIG:A:MODE?")
    scpi_write("TRIG:A:MODE NORM")
    scpi_query("TRIG:A:MODE?")


def test_acq_type():
    print_header("ACQ TYPE (WORKING)")
    scpi_query("ACQ:TYPE?")
    scpi_write("ACQ:TYPE ROLL")
    scpi_query("ACQ:TYPE?")
    scpi_write("ACQ:TYPE REFresh")
    scpi_query("ACQ:TYPE?")


def test_acq_state():
    print_header("ACQ STATE (SHOULD WORK)")
    scpi_query("ACQ:STATE?")
    scpi_write("ACQ:STATE RUN")
    scpi_write("ACQ:STATE STOP")


def test_run_stop():
    print_header("RUN / STOP (CLASSIC)")
    scpi_write("RUN")
    scpi_write("STOP")
    scpi_write("RUNSingle")
    scpi_write("RUNSINGLE")
    scpi_write("SINGLE")
    scpi_write("SINGle")


def test_single():
    print_header("SINGLE / STOPAFTER")
    scpi_write("ACQ:A:STOPAFTER SEQ")
    scpi_write("ACQ:A:STATE RUN")


def test_screenshot():
    print_header("SCREENSHOT")
    scpi_query("HCOPy:DATA?")


def test_overviews():
    print_header("OVERVIEWS of different parts")
    scpi_query("ACQ?")
    scpi_query("TRIG?")
    scpi_query("HCOP?")
    scpi_query("SYST?")


# ----------------------------
# MAIN
# ----------------------------
if __name__ == "__main__":

    clear_errors()

    test_ident()
    test_trigger()
    test_acq_type()
    test_acq_state()
    test_run_stop()
    test_single()
    test_screenshot()
    test_overviews()

    print("\nDONE.")