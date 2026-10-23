"""
EFI System Partition (ESP) Scanner for NextBoot.
Inspects the EFI partition to discover bootloaders installed on disk that may or may not be in NVRAM.
"""

import os
import subprocess
from typing import List, Dict, Any, Optional

class ESPBootloader:
    """Represents a bootloader found directly on the EFI System Partition."""
    def __init__(self, distro_folder: str, file_path: str, efi_name: str, suggested_name: str, os_family: str):
        self.distro_folder = distro_folder
        self.file_path = file_path        # e.g. \EFI\ubuntu\shimx64.efi
        self.efi_name = efi_name          # e.g. shimx64.efi
        self.suggested_name = suggested_name # e.g. Ubuntu (shimx64)
        self.os_family = os_family

    def to_dict(self) -> Dict[str, Any]:
        return {
            "distro_folder": self.distro_folder,
            "file_path": self.file_path,
            "efi_name": self.efi_name,
            "suggested_name": self.suggested_name,
            "os_family": self.os_family
        }


class ESPScanner:
    """Mounts the ESP partition temporarily to inspect installed EFI bootloaders."""

    KNOWN_DISTRO_MAP = {
        "ubuntu": ("Ubuntu Linux", "ubuntu"),
        "fedora": ("Fedora Linux", "fedora"),
        "debian": ("Debian Linux", "debian"),
        "arch": ("Arch Linux", "arch"),
        "mint": ("Linux Mint", "mint"),
        "pop": ("Pop!_OS", "pop_os"),
        "manjaro": ("Manjaro Linux", "manjaro"),
        "opensuse": ("openSUSE", "opensuse"),
        "kali": ("Kali Linux", "kali"),
        "zorin": ("Zorin OS", "zorin"),
        "steamos": ("SteamOS", "steamos"),
        "refind": ("rEFInd Boot Manager", "grub"),
        "systemd": ("systemd-boot", "grub"),
        "microsoft": ("Windows Boot Manager", "windows"),
        "boot": ("Default UEFI Fallback", "generic"),
        "oc": ("OpenCore (macOS)", "macos"),
        "clover": ("Clover Bootloader", "macos"),
    }

    def __init__(self, mount_letter: str = "S:"):
        self.mount_letter = mount_letter
        if not self.mount_letter.endswith(":"):
            self.mount_letter += ":"

    def _get_free_drive_letter(self) -> str:
        """Finds an unused drive letter for mounting."""
        used = set()
        for drive in "DEFGHIJKLMNOPQRSTUVWXYZ":
            if os.path.exists(f"{drive}:\\"):
                used.add(drive)
        for drive in "SZYXWVUT":
            if drive not in used:
                return f"{drive}:"
        return "S:"

    def mount_esp(self) -> bool:
        """Mounts EFI partition to selected drive letter."""
        letter = self.mount_letter
        try:
            res = subprocess.run(
                ["mountvol", letter, "/S"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            return res.returncode == 0
        except Exception:
            return False

    def unmount_esp(self) -> bool:
        """Unmounts the EFI partition."""
        letter = self.mount_letter
        try:
            res = subprocess.run(
                ["mountvol", letter, "/D"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            return res.returncode == 0
        except Exception:
            return False

    def scan_esp(self) -> List[ESPBootloader]:
        """
        Mounts the ESP partition, inspects \\EFI folder, and unmounts cleanly.
        Returns a list of detected ESPBootloader objects.
        """
        self.mount_letter = self._get_free_drive_letter()
        if not self.mount_esp():
            return []

        found_loaders = []
        try:
            efi_root = os.path.join(self.mount_letter + "\\", "EFI")
            if os.path.exists(efi_root):
                for folder in os.listdir(efi_root):
                    folder_path = os.path.join(efi_root, folder)
                    if not os.path.isdir(folder_path):
                        continue

                    folder_lower = folder.lower()
                    suggested_title, os_family = self.KNOWN_DISTRO_MAP.get(
                        folder_lower,
                        (f"{folder.capitalize()} (EFI)", "other")
                    )

                    # Scan for .efi files inside this folder
                    try:
                        for fname in os.listdir(folder_path):
                            if fname.lower().endswith(".efi"):
                                rel_path = f"\\EFI\\{folder}\\{fname}"
                                loader = ESPBootloader(
                                    distro_folder=folder,
                                    file_path=rel_path,
                                    efi_name=fname,
                                    suggested_name=f"{suggested_title} [{fname}]",
                                    os_family=os_family
                                )
                                found_loaders.append(loader)
                    except Exception:
                        pass
        finally:
            self.unmount_esp()

        return found_loaders
