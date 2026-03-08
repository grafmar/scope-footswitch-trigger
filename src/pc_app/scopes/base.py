import pyvisa


# ----------------------------
# Base Scope
# ----------------------------
class BaseScope:

    def __init__(self, scope: pyvisa.resources.Resource, log):
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