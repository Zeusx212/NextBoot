"""
Comprehensive unit test suite for NextBoot.
Tests OS detection, BCD parsing, boot management, and simulation workflows.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.os_detector import OSDetector, OSEntry
from core.boot_manager import BootManager

class TestNextBootSuite(unittest.TestCase):

    def setUp(self):
        self.detector = OSDetector()
        self.boot_mgr = BootManager(simulate=True)

    def test_distro_classification(self):
        """Test that different Linux distros and Windows versions are categorized accurately."""
        test_cases = [
            ("ubuntu", r"\EFI\UBUNTU\SHIMX64.EFI", "ubuntu"),
            ("Fedora Workstation", r"\EFI\FEDORA\SHIMX64.EFI", "fedora"),
            ("Arch Linux", r"\EFI\ARCH\GRUBX64.EFI", "arch"),
            ("Linux Mint 21", r"\EFI\MINT\GRUBX64.EFI", "mint"),
            ("Debian GNU/Linux", r"\EFI\DEBIAN\GRUBX64.EFI", "debian"),
            ("Pop!_OS 22.04", r"\EFI\SYSTEMD\SYSTEMD-BOOTX64.EFI", "pop_os"),
            ("Windows 11 Pro", r"\Windows\system32\winload.efi", "windows"),
            ("Windows 10 Enterprise", r"\Windows\system32\winload.efi", "windows"),
            ("OpenCore Bootloader", r"\EFI\OC\OPENCORE.EFI", "macos"),
            ("Realtek PCIe GBE", "", "hardware"),
        ]

        for desc, path, expected_family in test_cases:
            entry = self.detector.classify_entry({
                "identifier": "{12345678-1234-1234-1234-123456789abc}",
                "description": desc,
                "path": path,
                "header": "Firmware Application"
            })
            self.assertEqual(
                entry.os_family,
                expected_family,
                f"Failed classification for '{desc}' (got '{entry.os_family}', expected '{expected_family}')"
            )

    def test_boot_sequence_simulation(self):
        """Test that boot sequence commands are formed properly for firmware and osloader entries."""
        ubuntu_entry = OSEntry(
            identifier="{fa6c9a30-84c1-11ee-8bb4-806e6f6e6963}",
            name="Ubuntu 24.04",
            entry_type="firmware_app",
            os_family="ubuntu"
        )
        success, msg = self.boot_mgr.set_one_time_boot(ubuntu_entry)
        self.assertTrue(success)
        self.assertIn("Ubuntu 24.04", msg)

        win10_entry = OSEntry(
            identifier="{51821213-9830-11eb-bc82-00155d010b00}",
            name="Windows 10",
            entry_type="osloader",
            os_family="windows"
        )
        success_win, msg_win = self.boot_mgr.set_one_time_boot(win10_entry)
        self.assertTrue(success_win)
        self.assertIn("Windows 10", msg_win)

    def test_clear_and_reboot_simulation(self):
        """Test clear one-time boot and reboot simulation actions."""
        res, msg = self.boot_mgr.clear_one_time_boot()
        self.assertTrue(res)

        res_bios, msg_bios = self.boot_mgr.reboot_to_uefi_firmware()
        self.assertTrue(res_bios)

        res_rec, msg_rec = self.boot_mgr.reboot_to_recovery_menu()
        self.assertTrue(res_rec)

    def test_demo_entries_fallback(self):
        """Verify demo entries are returned in simulation or unprivileged mode."""
        entries = self.detector.detect_all(simulate_if_unprivileged=True)
        self.assertGreaterEqual(len(entries), 3)
        names = [e.name for e in entries]
        self.assertTrue(any("Windows" in n for n in names))
        self.assertTrue(any("Ubuntu" in n for n in names))

if __name__ == "__main__":
    unittest.main()
