"""
Unit tests for Universal BIOS & Firmware Update Assistant
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.universal_bios_updater import UniversalBIOSUpdater, VendorProfile, BIOSImageInfo

class TestUniversalBIOSUpdater(unittest.TestCase):

    def setUp(self):
        self.updater = UniversalBIOSUpdater(simulate=True)
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_vendor_profile_detection(self):
        prof = self.updater.get_vendor_profile()
        self.assertIsNotNone(prof)
        self.assertIn(prof.vendor_key, ["gigabyte", "asus", "msi", "asrock", "dell", "hp", "lenovo", "generic"])
        self.assertTrue(len(prof.flashing_utility) > 0)
        self.assertTrue(len(prof.instructions) >= 3)
        self.assertTrue(len(prof.shortcut_hint) > 0)

    def test_vendor_profiles_mocking(self):
        # 1. Gigabyte
        with patch.object(self.updater, 'detect_hardware', return_value={"manufacturer": "Gigabyte Technology Co., Ltd.", "product": "B550M DS3H"}):
            p_giga = self.updater.get_vendor_profile()
            self.assertEqual(p_giga.vendor_key, "gigabyte")
            self.assertEqual(p_giga.flashback_filename, "GIGABYTE.bin")
            self.assertIn("Q-Flash", p_giga.flashing_utility)

        # 2. ASUS
        with patch.object(self.updater, 'detect_hardware', return_value={"manufacturer": "ASUSTeK COMPUTER INC.", "product": "ROG STRIX B550-F"}):
            p_asus = self.updater.get_vendor_profile()
            self.assertEqual(p_asus.vendor_key, "asus")
            self.assertTrue(p_asus.flashback_filename.endswith(".CAP"))
            self.assertIn("EZ Flash", p_asus.flashing_utility)

        # 3. MSI
        with patch.object(self.updater, 'detect_hardware', return_value={"manufacturer": "Micro-Star International Co., Ltd.", "product": "MAG B550 TOMAHAWK"}):
            p_msi = self.updater.get_vendor_profile()
            self.assertEqual(p_msi.vendor_key, "msi")
            self.assertEqual(p_msi.flashback_filename, "MSI.ROM")
            self.assertIn("M-Flash", p_msi.flashing_utility)

        # 4. ASRock
        with patch.object(self.updater, 'detect_hardware', return_value={"manufacturer": "ASRock Inc.", "product": "B550 Phantom Gaming 4"}):
            p_asrock = self.updater.get_vendor_profile()
            self.assertEqual(p_asrock.vendor_key, "asrock")
            self.assertIn("Instant Flash", p_asrock.flashing_utility)

        # 5. Dell
        with patch.object(self.updater, 'detect_hardware', return_value={"manufacturer": "Dell Inc.", "product": "OptiPlex 7090"}):
            p_dell = self.updater.get_vendor_profile()
            self.assertEqual(p_dell.vendor_key, "dell")
            self.assertIn("Capsule", p_dell.flashing_utility)

    def test_storage_targets(self):
        targets = self.updater.get_storage_targets()
        self.assertIsInstance(targets, list)
        for t in targets:
            self.assertTrue(len(t.letter) == 1)
            self.assertTrue(t.total_gb >= 0)

    def test_analyze_firmware_file_synthetic(self):
        # Create a synthetic 16MB AMI Aptio firmware image containing target model string
        fw_path = os.path.join(self.test_dir, "B550MDS3H.bin")
        target_model = "B550M DS3H"
        with patch.object(self.updater, 'detect_hardware', return_value={"manufacturer": "Gigabyte", "product": target_model}):
            with open(fw_path, "wb") as f:
                # b"_FVH" header + model name + padded to exact 16MB (16777216 bytes)
                payload = b"_FVH\x00" + b"AMIAPTIO" + b"__" + target_model.encode("ascii")
                f.write(payload)
                f.write(b"\x00" * (16 * 1024 * 1024 - len(payload)))

            info = self.updater.analyze_firmware_file(fw_path)
            self.assertEqual(info.file_size, 16 * 1024 * 1024)
            self.assertTrue(info.is_valid_spi_size)
            self.assertIn("AMI", info.format_type)
            self.assertTrue(info.matches_detected_board)
            self.assertIn("B550M DS3H", info.matched_strings)
            self.assertTrue(len(info.sha256) == 64)

    def test_analyze_asus_capsule_file(self):
        # Create a synthetic 16MB + 2048 bytes ASUS .CAP image
        cap_path = os.path.join(self.test_dir, "ROG.CAP")
        with patch.object(self.updater, 'detect_hardware', return_value={"manufacturer": "ASUS", "product": "ROG STRIX"}):
            with open(cap_path, "wb") as f:
                header = b"$CAPSULE$" + b"\x00" * (2048 - 9)
                body = b"_FVH" + b"\x00" * (16 * 1024 * 1024 - 4)
                f.write(header + body)

            info = self.updater.analyze_firmware_file(cap_path)
            self.assertEqual(info.file_size, 16 * 1024 * 1024 + 2048)
            self.assertTrue(info.is_valid_spi_size)
            self.assertTrue(info.has_capsule_header)
            self.assertIn("Capsule", info.format_type)

    def test_stage_firmware_real_copy_and_verification(self):
        # Test real file staging into temporary directory with SHA-256 verification
        real_updater = UniversalBIOSUpdater(simulate=False)
        src_file = os.path.join(self.test_dir, "firmware.bin")
        content = b"_FVH\x00TEST_IMAGE_DATA_12345"
        with open(src_file, "wb") as f:
            f.write(content)

        dest_dir = os.path.join(self.test_dir, "usb_mock")
        os.makedirs(dest_dir, exist_ok=True)

        with patch.object(real_updater, 'detect_hardware', return_value={"manufacturer": "Gigabyte", "product": "B550M"}):
            success, msg, created = real_updater.stage_firmware(src_file, dest_dir, create_flashback_copy=True)
            self.assertTrue(success)
            self.assertIn("Successfully staged", msg)
            self.assertEqual(len(created), 2) # Original + GIGABYTE.bin
            self.assertTrue(os.path.isfile(os.path.join(dest_dir, "firmware.bin")))
            self.assertTrue(os.path.isfile(os.path.join(dest_dir, "GIGABYTE.bin")))

            # Verify contents of both files
            with open(os.path.join(dest_dir, "GIGABYTE.bin"), "rb") as f:
                self.assertEqual(f.read(), content)

    def test_reboot_to_flasher_simulation(self):
        success, msg = self.updater.reboot_to_firmware_flasher()
        self.assertTrue(success)
        self.assertIn("SIMULATION", msg)

if __name__ == "__main__":
    unittest.main()
