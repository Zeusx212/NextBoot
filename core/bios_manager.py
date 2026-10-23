"""
BIOS & Firmware Manager module for NextBoot.
Provides UEFI boot order editing, timeout configuration, motherboard diagnostics,
and essential dual-boot tweaks (Fast Startup & RTC UTC clock sync).
"""

import os
import re
import subprocess
import winreg
from typing import Dict, List, Tuple, Any, Optional
from core.os_detector import OSEntry

class BIOSManager:
    """Controls motherboard firmware diagnostics, boot order, and dual-boot system tweaks."""

    def __init__(self, simulate: bool = False):
        self.simulate = simulate

    def _execute(self, cmd: List[str]) -> Tuple[bool, str]:
        """Runs a system command with error capture."""
        if self.simulate:
            return True, f"[SIMULATION] Command would execute: {' '.join(cmd)}"

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            output = (proc.stdout + " " + proc.stderr).strip()
            return (proc.returncode == 0), output
        except Exception as e:
            return False, str(e)

    def get_firmware_diagnostics(self) -> Dict[str, Any]:
        """Reads motherboard, BIOS version, Secure Boot, and dual-boot status from registry and system."""
        info = {
            "manufacturer": "Unknown",
            "product": "Unknown Motherboard",
            "bios_version": "Unknown",
            "bios_date": "Unknown",
            "secure_boot": None,
            "fast_startup": False,
            "rtc_utc": False,
            "timeout": 30
        }

        # 1. Motherboard & BIOS version
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

        # 2. Secure Boot status
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\SecureBoot\State") as key:
                val = winreg.QueryValueEx(key, "UEFISecureBootEnabled")[0]
                info["secure_boot"] = (val == 1)
        except Exception:
            info["secure_boot"] = None

        # 3. Windows Fast Startup (HiberbootEnabled)
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Power") as key:
                val = winreg.QueryValueEx(key, "HiberbootEnabled")[0]
                info["fast_startup"] = (val == 1)
        except Exception:
            info["fast_startup"] = False

        # 4. RTC Hardware Clock in UTC (RealTimeIsUniversal)
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\TimeZoneInformation") as key:
                val = winreg.QueryValueEx(key, "RealTimeIsUniversal")[0]
                info["rtc_utc"] = (val == 1)
        except Exception:
            info["rtc_utc"] = False

        # 5. Boot Timeout
        info["timeout"] = self.get_boot_timeout()

        return info

    def get_boot_timeout(self) -> int:
        """Retrieves current boot menu timeout in seconds from BCD."""
        if self.simulate:
            return 10
        try:
            proc = subprocess.run(
                ["bcdedit", "/enum", "{bootmgr}"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            for line in proc.stdout.splitlines():
                if "timeout" in line.lower():
                    parts = line.strip().split()
                    if len(parts) >= 2 and parts[-1].isdigit():
                        return int(parts[-1])
        except Exception:
            pass
        return 30

    def set_boot_timeout(self, seconds: int) -> Tuple[bool, str]:
        """Sets the boot menu timeout in seconds."""
        sec = max(0, min(120, int(seconds)))
        res1, out1 = self._execute(["bcdedit", "/timeout", str(sec)])
        # Also apply to fwbootmgr for UEFI motherboard boot manager
        res2, out2 = self._execute(["bcdedit", "/set", "{fwbootmgr}", "timeout", str(sec)])

        if res1 or res2:
            return True, f"Boot timeout successfully set to {sec} second(s)."
        return False, f"Failed to set boot timeout: {out1}"

    def set_fast_startup(self, enable: bool) -> Tuple[bool, str]:
        """
        Enables or disables Windows Fast Startup.
        Disabling Fast Startup is highly recommended for multi-boot because it
        prevents NTFS drive locking and Linux filesystem mount errors.
        """
        val = 1 if enable else 0
        action = "enabled" if enable else "disabled (Recommended for dual-boot)"
        if self.simulate:
            return True, f"[SIMULATION] Windows Fast Startup {action}."

        try:
            key_path = r"SYSTEM\CurrentControlSet\Control\Session Manager\Power"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "HiberbootEnabled", 0, winreg.REG_DWORD, val)

            return True, f"Windows Fast Startup has been {action}."
        except PermissionError:
            return False, "Access denied. Administrator privileges are required to toggle Fast Startup."
        except Exception as e:
            return False, f"Error configuring Fast Startup: {e}"

    def set_rtc_utc(self, enable: bool) -> Tuple[bool, str]:
        """
        Enables or disables RealTimeIsUniversal (Hardware RTC clock in UTC).
        Linux distributions default to storing UTC in hardware RTC.
        Setting this to True in Windows prevents the clock from jumping back/forth.
        """
        val = 1 if enable else 0
        action = "configured to UTC (Fixes Linux time conflict)" if enable else "restored to Local Time"
        if self.simulate:
            return True, f"[SIMULATION] Hardware RTC clock {action}."

        try:
            key_path = r"SYSTEM\CurrentControlSet\Control\TimeZoneInformation"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "RealTimeIsUniversal", 0, winreg.REG_DWORD, val)

            return True, f"Hardware RTC clock has been {action}."
        except PermissionError:
            return False, "Access denied. Administrator privileges are required to modify clock synchronization."
        except Exception as e:
            return False, f"Error configuring RTC Clock: {e}"

    def set_uefi_boot_order(self, ordered_identifiers: List[str]) -> Tuple[bool, str]:
        """
        Updates the motherboard UEFI NVRAM boot order (displayorder) permanently.
        """
        if not ordered_identifiers:
            return False, "Identifier list cannot be empty."

        cmd = ["bcdedit", "/set", "{fwbootmgr}", "displayorder"] + ordered_identifiers
        success, out = self._execute(cmd)
        if success:
            # Also set the first item as the default boot entry
            self._execute(["bcdedit", "/set", "{fwbootmgr}", "default", ordered_identifiers[0]])
            return True, "Motherboard UEFI boot order updated successfully."

        # Fallback to standard bootmgr displayorder if fwbootmgr fails
        cmd2 = ["bcdedit", "/displayorder"] + ordered_identifiers
        s2, o2 = self._execute(cmd2)
        if s2:
            return True, "Boot Manager display order updated successfully."

        return False, f"Failed to update boot order: {out} / {o2}"
