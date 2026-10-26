"""
Universal BIOS & Firmware Update Assistant for NextBoot.
Supports multi-vendor motherboard identification (Gigabyte, ASUS, MSI, ASRock, Dell, HP, Lenovo),
firmware image binary analysis, integrity validation, FAT32 Flashback staging,
and 1-click seamless reboot directly into the native UEFI BIOS flashing interface.
"""

import os
import re
import sys
import shutil
import hashlib
import string
import ctypes
import winreg
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Optional

@dataclass
class VendorProfile:
    """Motherboard vendor specifications and flashing guidelines."""
    vendor_key: str              # 'gigabyte', 'asus', 'msi', 'asrock', 'dell', 'hp', 'lenovo', 'generic'
    display_name: str            # 'Gigabyte / AORUS'
    raw_manufacturer: str        # 'Gigabyte Technology Co., Ltd.'
    raw_product: str             # 'B550M DS3H'
    flashing_utility: str        # 'Q-Flash & Q-Flash Plus'
    flashback_filename: Optional[str] # 'GIGABYTE.bin'
    recommended_fs: str          # 'FAT32 / FAT16'
    shortcut_hint: str           # 'Press <End> or <F8> during boot'
    instructions: List[str]      # Step-by-step guidance
    badge_color: str             # '#f97316' (Orange for Gigabyte, '#ef4444' for ASUS ROG, etc.)

@dataclass
class BIOSImageInfo:
    """Detailed metadata and verification report for a selected firmware file."""
    file_path: str
    file_name: str
    file_size: int
    file_size_mb: float
    sha256: str
    format_type: str             # 'AMI Aptio V / IV', 'ASUS AMI Capsule (.CAP)', etc.
    is_valid_spi_size: bool
    has_capsule_header: bool
    matches_detected_board: bool
    matched_strings: List[str] = field(default_factory=list)
    recommended_staged_name: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

@dataclass
class StorageTarget:
    """A destination drive detected for staging firmware."""
    letter: str
    root: str
    label: str
    fs: str
    is_removable: bool
    is_fat32: bool
    free_gb: float
    total_gb: float

    @property
    def display_text(self) -> str:
        tag = "[USB FAT32 - Recommended]" if (self.is_removable and self.is_fat32) else \
              "[FAT32]" if self.is_fat32 else \
              f"[{self.fs or 'Drive'}]"
        lbl = f" '{self.label}'" if self.label else ""
        return f"{self.letter}: {lbl} ({tag}, {self.free_gb:.1f} GB free)"

class UniversalBIOSUpdater:
    """Core engine for universal motherboard firmware analysis, staging, and reboot coordination."""

    # Standard SPI flash memory sizes (bytes)
    STANDARD_SPI_SIZES = {
        4 * 1024 * 1024: "4 MB (32 Mbit)",
        8 * 1024 * 1024: "8 MB (64 Mbit)",
        16 * 1024 * 1024: "16 MB (128 Mbit)",
        32 * 1024 * 1024: "32 MB (256 Mbit)",
        64 * 1024 * 1024: "64 MB (512 Mbit)"
    }
    # ASUS Capsule header is exactly 2048 bytes (0x800)
    CAPSULE_HEADER_SIZE = 2048

    def __init__(self, simulate: bool = False):
        self.simulate = simulate

    def detect_hardware(self) -> Dict[str, str]:
        """Queries SMBIOS and registry for motherboard manufacturer, product model, and current BIOS."""
        info = {
            "manufacturer": "Unknown",
            "product": "Unknown Motherboard",
            "bios_version": "Unknown",
            "bios_date": "Unknown"
        }
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\BIOS") as key:
                try: info["manufacturer"] = winreg.QueryValueEx(key, "BaseBoardManufacturer")[0]
                except Exception: pass
                try: info["product"] = winreg.QueryValueEx(key, "BaseBoardProduct")[0]
                except Exception: pass
                try: info["bios_version"] = winreg.QueryValueEx(key, "BIOSVersion")[0]
                except Exception: pass
                try: info["bios_date"] = winreg.QueryValueEx(key, "BIOSReleaseDate")[0]
                except Exception: pass
        except Exception:
            pass
        return info

    def get_vendor_profile(self) -> VendorProfile:
        """Determines vendor-specific flashing protocol, Flashback naming, and safety instructions."""
        hw = self.detect_hardware()
        mfg = hw["manufacturer"].strip()
        prod = hw["product"].strip()
        mfg_lower = mfg.lower()

        # 1. Gigabyte / AORUS
        if any(k in mfg_lower for k in ("gigabyte", "aorus")):
            return VendorProfile(
                vendor_key="gigabyte",
                display_name="Gigabyte / AORUS",
                raw_manufacturer=mfg,
                raw_product=prod,
                flashing_utility="Q-Flash & Q-Flash Plus",
                flashback_filename="GIGABYTE.bin",
                recommended_fs="FAT32 / FAT16",
                shortcut_hint="Press <End> or <F8> during boot, or in BIOS Setup",
                instructions=[
                    "Format a USB drive as FAT32 (MBR partition table).",
                    "NextBoot will stage the firmware and automatically create 'GIGABYTE.bin' for Q-Flash Plus.",
                    "For In-BIOS Flashing: Click 'Reboot to Flasher', press <End> to enter Q-Flash, and select the file.",
                    "For Q-Flash Plus (Hardware Button): Power off system, plug USB into the white 'BIOS' USB port on rear I/O, and press the Q-Flash Plus button until the LED blinks.",
                    "CAUTION: Never turn off power or remove the flash drive while flashing is underway."
                ],
                badge_color="#f97316" # Vibrant Orange
            )

        # 2. ASUS / ROG / TUF / ProArt
        elif any(k in mfg_lower for k in ("asustek", "asus", "republic of gamers")):
            # Derive ASUS Flashback model name if possible, or fallback
            clean_prod = re.sub(r"[^A-Za-z0-9]", "", prod).upper()
            asus_fb_name = f"{clean_prod[:8]}.CAP" if clean_prod else "ASUS.CAP"
            return VendorProfile(
                vendor_key="asus",
                display_name="ASUS / ROG / TUF",
                raw_manufacturer=mfg,
                raw_product=prod,
                flashing_utility="EZ Flash 3 & USB BIOS Flashback",
                flashback_filename=asus_fb_name,
                recommended_fs="FAT32 / FAT16",
                shortcut_hint="Press <Del> or <F2> -> Advanced (F7) -> Tool -> EZ Flash 3",
                instructions=[
                    "ASUS firmware uses encapsulated .CAP files with an RSA security signature.",
                    "NextBoot stages your .CAP file and prepares the BIOS Flashback target name.",
                    "For EZ Flash 3: Click 'Reboot to Flasher', navigate to Tool -> ASUS EZ Flash 3, select the drive and file.",
                    "For USB Flashback: Plug FAT32 USB into the designated BIOS Flashback port, hold button for 3 seconds until the LED starts blinking.",
                    "CAUTION: Do not shut down or disconnect power until flashing is 100% complete."
                ],
                badge_color="#dc2626" # ASUS ROG Red
            )

        # 3. MSI (Micro-Star International)
        elif any(k in mfg_lower for k in ("msi", "micro-star")):
            return VendorProfile(
                vendor_key="msi",
                display_name="MSI / MEG / MPG / MAG",
                raw_manufacturer=mfg,
                raw_product=prod,
                flashing_utility="M-Flash & Flash BIOS Button",
                flashback_filename="MSI.ROM",
                recommended_fs="FAT32",
                shortcut_hint="In BIOS Setup, click <M-Flash> on bottom-left",
                instructions=[
                    "Format a USB drive with FAT32.",
                    "NextBoot stages the ROM file and automatically creates 'MSI.ROM' for the Flash BIOS button.",
                    "For M-Flash: Click 'Reboot to Flasher', click 'M-Flash' in BIOS. The motherboard will restart into M-Flash mode.",
                    "For Flash BIOS Button: Plug USB into dedicated port, press Flash BIOS button for 3 seconds. The LED will blink for 5-7 minutes.",
                    "CAUTION: Ensure continuous AC power throughout the flash process."
                ],
                badge_color="#ef4444" # MSI Dragon Red
            )

        # 4. ASRock
        elif "asrock" in mfg_lower:
            return VendorProfile(
                vendor_key="asrock",
                display_name="ASRock / Taichi",
                raw_manufacturer=mfg,
                raw_product=prod,
                flashing_utility="Instant Flash & BIOS Flashback",
                flashback_filename="CREATIVE.ROM",
                recommended_fs="FAT32",
                shortcut_hint="Press <F6> during boot, or Tool -> Instant Flash",
                instructions=[
                    "Save the BIOS ROM file onto the root of a FAT32 USB drive.",
                    "Click 'Reboot to Flasher', then press <F6> during boot to jump straight into Instant Flash.",
                    "Select your BIOS ROM from the menu and confirm.",
                    "CAUTION: Do not power down the system while programming SPI flash."
                ],
                badge_color="#0284c7" # ASRock Blue
            )

        # 5. Dell / Alienware
        elif "dell" in mfg_lower or "alienware" in mfg_lower:
            return VendorProfile(
                vendor_key="dell",
                display_name="Dell / Alienware",
                raw_manufacturer=mfg,
                raw_product=prod,
                flashing_utility="BIOS Flash Update & UEFI Capsule",
                flashback_filename=None,
                recommended_fs="FAT32",
                shortcut_hint="Press <F12> during boot -> Select 'BIOS Flash Update'",
                instructions=[
                    "Dell distributes BIOS updates as signed executables or capsule files.",
                    "Save the update file to a FAT32 USB flash drive or system root.",
                    "Press <F12> during boot to access the One-Time Boot Menu, select 'BIOS Flash Update', pick the file, and proceed.",
                    "Alternatively, run the Dell BIOS executable inside Windows with all other programs closed."
                ],
                badge_color="#0ea5e9" # Dell Blue
            )

        # 6. HP / Hewlett-Packard / Omen
        elif any(k in mfg_lower for k in ("hp", "hewlett-packard")):
            return VendorProfile(
                vendor_key="hp",
                display_name="HP / Omen / Pavilion",
                raw_manufacturer=mfg,
                raw_product=prod,
                flashing_utility="HP BIOS Update & UEFI Diagnostics",
                flashback_filename=None,
                recommended_fs="FAT32",
                shortcut_hint="Press <F2> during boot -> Firmware Management",
                instructions=[
                    "HP supports automated Windows execution or USB pre-boot update.",
                    "Copy the HP firmware package to a FAT32 USB flash drive.",
                    "Boot into HP UEFI Hardware Diagnostics (<F2> or <Esc> at startup), choose 'Firmware Management', and update.",
                    "Emergency recovery: Press and hold <Windows Key + B> during power-on."
                ],
                badge_color="#2563eb" # HP Blue
            )

        # 7. Lenovo / ThinkPad / Legion
        elif "lenovo" in mfg_lower:
            return VendorProfile(
                vendor_key="lenovo",
                display_name="Lenovo / ThinkPad / Legion",
                raw_manufacturer=mfg,
                raw_product=prod,
                flashing_utility="Lenovo UEFI Flash Update & ESRT Capsule",
                flashback_filename=None,
                recommended_fs="FAT32",
                shortcut_hint="Press <F12> or <Enter> at startup -> BIOS Setup",
                instructions=[
                    "Lenovo updates are packaged with automated UEFI capsule injectors.",
                    "Ensure AC adapter is securely plugged in and battery is charged above 30%.",
                    "Launch the update package or boot from a prepared Lenovo UEFI USB drive."
                ],
                badge_color="#e11d48" # Lenovo Crimson
            )

        # 8. Generic / Unknown Motherboard
        else:
            return VendorProfile(
                vendor_key="generic",
                display_name=f"{mfg or 'Generic'} Motherboard",
                raw_manufacturer=mfg or "Unknown Vendor",
                raw_product=prod or "Standard Motherboard",
                flashing_utility="Universal UEFI Firmware Utility",
                flashback_filename="BIOS.ROM",
                recommended_fs="FAT32",
                shortcut_hint="Press <Del> or <F2> to enter BIOS setup",
                instructions=[
                    "Ensure your USB drive is formatted as FAT32.",
                    "Copy your unzipped BIOS ROM file directly to the root of the USB drive.",
                    "Use NextBoot's 'Reboot to Flasher' button to enter BIOS setup directly.",
                    "Locate your motherboard's built-in flash utility (e.g., in 'Tools' or 'Advanced' menu)."
                ],
                badge_color="#6366f1" # Indigo
            )

    def get_storage_targets(self) -> List[StorageTarget]:
        """Scans system for connected drives, prioritizing FAT32 USB flash drives."""
        targets: List[StorageTarget] = []
        if os.name != "nt":
            return targets

        try:
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
            for letter in string.ascii_uppercase:
                if bitmask & 1:
                    root = f"{letter}:\\"
                    dtype = ctypes.windll.kernel32.GetDriveTypeW(root)
                    # DRIVE_REMOVABLE = 2, DRIVE_FIXED = 3
                    if dtype in (2, 3):
                        fs_buf = ctypes.create_unicode_buffer(261)
                        name_buf = ctypes.create_unicode_buffer(261)
                        serial = ctypes.c_ulong()
                        max_len = ctypes.c_ulong()
                        flags = ctypes.c_ulong()
                        ctypes.windll.kernel32.GetVolumeInformationW(
                            root, name_buf, 260,
                            ctypes.byref(serial), ctypes.byref(max_len), ctypes.byref(flags),
                            fs_buf, 260
                        )

                        free_bytes = ctypes.c_ulonglong(0)
                        total_bytes = ctypes.c_ulonglong(0)
                        total_free = ctypes.c_ulonglong(0)
                        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                            root, ctypes.byref(free_bytes), ctypes.byref(total_bytes), ctypes.byref(total_free)
                        )

                        fs_str = fs_buf.value.upper()
                        is_fat = "FAT" in fs_str
                        is_removable = (dtype == 2)

                        targets.append(StorageTarget(
                            letter=letter,
                            root=root,
                            label=name_buf.value,
                            fs=fs_buf.value,
                            is_removable=is_removable,
                            is_fat32=is_fat,
                            free_gb=free_bytes.value / (1024**3),
                            total_gb=total_bytes.value / (1024**3)
                        ))
                bitmask >>= 1
        except Exception:
            pass

        # Sort: Removable FAT32 first, then Fixed FAT32, then Removable others, then Fixed
        targets.sort(
            key=lambda t: (
                0 if (t.is_removable and t.is_fat32) else
                1 if t.is_fat32 else
                2 if t.is_removable else 3
            )
        )
        return targets

    def analyze_firmware_file(self, file_path: str) -> BIOSImageInfo:
        """
        Performs deep binary header inspection, SHA-256 calculation,
        SPI flash memory size validation, and motherboard model cross-referencing.
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)

        # 1. Calculate SHA-256
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256_hash.update(chunk)
        digest = sha256_hash.hexdigest().upper()

        # 2. Check SPI flash standard sizes
        is_exact_spi = file_size in self.STANDARD_SPI_SIZES
        is_capsule_spi = (file_size - self.CAPSULE_HEADER_SIZE) in self.STANDARD_SPI_SIZES
        is_valid_spi_size = is_exact_spi or is_capsule_spi

        # 3. Read first 64KB for binary headers
        with open(file_path, "rb") as f:
            head = f.read(65536)

        # Format detection
        format_type = "Generic Firmware Binary"
        has_capsule_header = False

        # Look for Firmware Volume Header: b"_FVH" (0x5F, 0x46, 0x56, 0x48)
        has_fvh = b"_FVH" in head

        # Check for ASUS / AMI Capsule Header
        if is_capsule_spi or (file_path.lower().endswith(".cap") and len(head) >= 2048):
            has_capsule_header = True
            format_type = "ASUS AMI Aptio Capsule (.CAP)"
        elif b"$AMIBOOT$" in head or b"AMIAPTIO" in head or (has_fvh and "ami" in head.lower()):
            format_type = "AMI Aptio V / IV UEFI Image"
        elif b"$_IFLASH_$" in head or b"$IBIOS$" in head:
            format_type = "InsydeH2O UEFI Image"
        elif has_fvh:
            format_type = "UEFI Firmware Volume (AMI/EDK2)"
        elif file_name.lower().endswith(".exe"):
            format_type = "Vendor Executable BIOS Installer"

        # 4. Model Verification: Search for current motherboard model inside image
        vendor_prof = self.get_vendor_profile()
        target_model = vendor_prof.raw_product.strip()
        matched_strings: List[str] = []
        matches_board = False

        if target_model and target_model != "Unknown Motherboard" and len(target_model) >= 3:
            # Prepare search tokens (e.g., 'B550M DS3H', 'B550M', 'DS3H')
            model_tokens = [target_model]
            subparts = re.findall(r"[A-Za-z0-9]+", target_model)
            if len(subparts) > 1:
                # Add full joined string (e.g. 'B550MDS3H')
                model_tokens.append("".join(subparts))
                for p in subparts:
                    if len(p) >= 4:
                        model_tokens.append(p)

            # Search binary image in chunks (both ASCII and UTF-16LE)
            try:
                with open(file_path, "rb") as f:
                    content = f.read(2 * 1024 * 1024) # Scan first 2MB (where SMBIOS/DMI tables live)
                    content_lower = content.lower()
                    for token in model_tokens:
                        t_ascii = token.lower().encode("ascii", errors="ignore")
                        t_utf16 = token.lower().encode("utf-16-le", errors="ignore")
                        if t_ascii in content_lower or t_utf16 in content_lower:
                            matched_strings.append(token)
                            matches_board = True
            except Exception:
                pass

        # 5. Warnings
        warnings: List[str] = []
        if not is_valid_spi_size and not file_name.lower().endswith(".exe"):
            warnings.append(
                f"File size ({file_size_mb:.2f} MB) is not a standard SPI flash chip multiple (8MB, 16MB, 32MB, 64MB)."
            )

        if target_model and not matches_board and not file_name.lower().endswith(".exe"):
            warnings.append(
                f"Could not verify motherboard model '{target_model}' inside the BIOS image. Ensure this file is for your exact board."
            )

        # Recommended flashback target name
        rec_name = vendor_prof.flashback_filename or file_name

        return BIOSImageInfo(
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
            file_size_mb=round(file_size_mb, 2),
            sha256=digest,
            format_type=format_type,
            is_valid_spi_size=is_valid_spi_size,
            has_capsule_header=has_capsule_header,
            matches_detected_board=matches_board,
            matched_strings=list(set(matched_strings)),
            recommended_staged_name=rec_name,
            warnings=warnings
        )

    def stage_firmware(
        self,
        source_file: str,
        target_drive_root: str,
        create_flashback_copy: bool = True
    ) -> Tuple[bool, str, List[str]]:
        """
        Copies the firmware image to the root of the destination drive.
        If requested, also creates the vendor-standardized Flashback copy (e.g. GIGABYTE.bin / MSI.ROM).
        Performs post-copy SHA-256 verification to ensure bit-perfect staging.
        """
        if not os.path.isfile(source_file):
            return False, f"Source file does not exist: {source_file}", []

        if not os.path.exists(target_drive_root):
            return False, f"Target destination does not exist: {target_drive_root}", []

        if self.simulate:
            sim_paths = [os.path.join(target_drive_root, os.path.basename(source_file))]
            prof = self.get_vendor_profile()
            if create_flashback_copy and prof.flashback_filename:
                sim_paths.append(os.path.join(target_drive_root, prof.flashback_filename))
            return True, f"[SIMULATION] Files would be staged to {target_drive_root}", sim_paths

        created_files: List[str] = []
        try:
            # 1. Compute source SHA-256
            src_sha = hashlib.sha256()
            with open(source_file, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    src_sha.update(chunk)
            source_digest = src_sha.hexdigest()

            # 2. Copy original file to target
            orig_dest = os.path.join(target_drive_root, os.path.basename(source_file))
            shutil.copy2(source_file, orig_dest)
            created_files.append(orig_dest)

            # 3. Create standardized Flashback copy if supported by vendor
            prof = self.get_vendor_profile()
            if create_flashback_copy and prof.flashback_filename:
                fb_dest = os.path.join(target_drive_root, prof.flashback_filename)
                # Avoid duplicating if source already has flashback name
                if os.path.basename(orig_dest).lower() != prof.flashback_filename.lower():
                    shutil.copy2(source_file, fb_dest)
                    created_files.append(fb_dest)

            # 4. Verify post-copy SHA-256 integrity on destination
            dst_sha = hashlib.sha256()
            with open(orig_dest, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    dst_sha.update(chunk)

            if dst_sha.hexdigest() != source_digest:
                return False, "Integrity verification failed! Staged file hash does not match source.", created_files

            msg = (
                f"Successfully staged firmware to '{target_drive_root}'.\n"
                f"Verified SHA-256: {source_digest.upper()}\n"
                f"Files created: {', '.join(os.path.basename(p) for p in created_files)}"
            )
            return True, msg, created_files

        except PermissionError:
            return False, "Permission denied. Administrator access is required to write to target root.", created_files
        except Exception as e:
            return False, f"Error staging firmware: {e}", created_files

    def reboot_to_firmware_flasher(self, delay_seconds: int = 0) -> Tuple[bool, str]:
        """
        Reboots the PC directly into the motherboard UEFI firmware setup interface,
        bypassing the need to spam keyboard keys during POST.
        """
        if self.simulate:
            return True, f"[SIMULATION] System would restart to UEFI firmware with {delay_seconds}s delay."

        cmd = ["shutdown", "/r", "/fw", "/t", str(max(0, delay_seconds)), "/f"]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            out = (proc.stdout + " " + proc.stderr).strip()
            if proc.returncode == 0:
                return True, "System reboot initiated. PC will restart directly into UEFI Firmware interface."
            else:
                # Fallback: attempt without /f or with 1s delay
                cmd2 = ["shutdown", "/r", "/fw", "/t", "1"]
                proc2 = subprocess.run(
                    cmd2,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                )
                if proc2.returncode == 0:
                    return True, "System reboot initiated into UEFI firmware."
                return False, f"Failed to initiate firmware reboot: {out}"
        except Exception as e:
            return False, str(e)
