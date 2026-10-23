"""
Unit tests for BIOSManager
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.bios_manager import BIOSManager

class TestBIOSManager(unittest.TestCase):

    def setUp(self):
        self.mgr = BIOSManager(simulate=True)

    def test_firmware_diagnostics_structure(self):
        diag = self.mgr.get_firmware_diagnostics()
        self.assertIn("manufacturer", diag)
        self.assertIn("product", diag)
        self.assertIn("bios_version", diag)
        self.assertIn("fast_startup", diag)
        self.assertIn("rtc_utc", diag)
        self.assertIn("timeout", diag)

    def test_timeout_simulation(self):
        success, msg = self.mgr.set_boot_timeout(15)
        self.assertTrue(success)
        self.assertIn("15 second(s)", msg)

    def test_fast_startup_simulation(self):
        success, msg = self.mgr.set_fast_startup(False)
        self.assertTrue(success)
        self.assertIn("disabled", msg.lower())

    def test_rtc_utc_simulation(self):
        success, msg = self.mgr.set_rtc_utc(True)
        self.assertTrue(success)
        self.assertIn("utc", msg.lower())

    def test_boot_order_simulation(self):
        guids = ["{fa6c9a30-84c1-11ee-8bb4-806e6f6e6963}", "{current}"]
        success, msg = self.mgr.set_uefi_boot_order(guids)
        self.assertTrue(success)

if __name__ == "__main__":
    unittest.main()
