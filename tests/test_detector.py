"""
Unit test for OSDetector
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.os_detector import OSDetector, OSEntry

SAMPLE_BCD_OUTPUT = r"""
Firmware Boot Manager
---------------------
identifier              {fwbootmgr}
displayorder            {bootmgr}
                        {7a56c42a-a92c-11ee-8261-806e6f6e6963}
                        {7a56c42b-a92c-11ee-8261-806e6f6e6963}
bootsequence            {7a56c42a-a92c-11ee-8261-806e6f6e6963}
default                 {bootmgr}
timeout                 0

Windows Boot Manager
--------------------
identifier              {bootmgr}
device                  partition=\Device\HarddiskVolume1
path                    \EFI\MICROSOFT\BOOT\BOOTMGFW.EFI
description             Windows Boot Manager
default                 {current}

Firmware Application (101fffff)
-------------------------------
identifier              {7a56c42a-a92c-11ee-8261-806e6f6e6963}
device                  partition=\Device\HarddiskVolume1
path                    \EFI\UBUNTU\SHIMX64.EFI
description             ubuntu

Firmware Application (101fffff)
-------------------------------
identifier              {7a56c42b-a92c-11ee-8261-806e6f6e6963}
device                  partition=\Device\HarddiskVolume1
path                    \EFI\FEDORA\SHIMX64.EFI
description             Fedora

Firmware Application (101fffff)
-------------------------------
identifier              {7a56c42d-a92c-11ee-8261-806e6f6e6963}
description             UEFI: IP4 Realtek PCIe GBE Family Controller

Windows Boot Loader
-------------------
identifier              {current}
device                  partition=C:
path                    \Windows\system32\winload.efi
description             Windows 11 Pro
"""

class TestOSDetector(unittest.TestCase):
    def test_parsing_and_classification(self):
        detector = OSDetector()
        blocks = detector.parse_raw_bcd_blocks(SAMPLE_BCD_OUTPUT)
        self.assertEqual(len(blocks), 6)

        # Set manager fields
        for b in blocks:
            ident = b.get("identifier", "").lower()
            if ident == "{fwbootmgr}":
                detector.firmware_bootsequence = b.get("bootsequence")
                detector.firmware_default = b.get("default")
            elif ident == "{bootmgr}":
                detector.bootmgr_default = b.get("default")

        entries = [detector.classify_entry(b) for b in blocks if b.get("identifier") not in ("{fwbootmgr}", "{bootmgr}")]
        self.assertEqual(len(entries), 4)

        # Check Ubuntu entry
        ubuntu = next(e for e in entries if "ubuntu" in e.name.lower())
        self.assertEqual(ubuntu.os_family, "ubuntu")
        self.assertEqual(ubuntu.entry_type, "firmware_app")
        self.assertTrue(ubuntu.is_next_boot) # It was in bootsequence!

        # Check Fedora entry
        fedora = next(e for e in entries if "fedora" in e.name.lower())
        self.assertEqual(fedora.os_family, "fedora")
        self.assertFalse(fedora.is_next_boot)

        # Check Windows 11 entry
        win11 = next(e for e in entries if "windows 11" in e.name.lower())
        self.assertEqual(win11.os_family, "windows")
        self.assertTrue(win11.is_current)

        # Check Hardware entry
        hw = next(e for e in entries if "realtek" in e.name.lower())
        self.assertEqual(hw.os_family, "hardware")
        self.assertEqual(hw.entry_type, "hardware")

if __name__ == "__main__":
    unittest.main()
