"""
Boot Manager module for NextBoot.
Controls one-time boot sequence, permanent default OS selection, and system restarts.
"""

import os
import subprocess
from typing import Tuple, Optional
from core.os_detector import OSEntry

class BootManager:
    """Manages BCD bootsequence configuration and system reboot triggers."""

    def __init__(self, simulate: bool = False):
        self.simulate = simulate
        self.log_history = []

    def _log(self, msg: str):
        self.log_history.append(msg)
        print(f"[BootManager] {msg}")

    def _execute(self, cmd: list) -> Tuple[bool, str]:
        """Runs a system command with error capture."""
        self._log(f"Executing: {' '.join(cmd)}")
        if self.simulate:
            self._log("[SIMULATION] Command would be executed in real mode.")
            return True, "[SIMULATION] Command executed successfully."

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
            if proc.returncode == 0:
                self._log(f"Success: {output}")
                return True, output
            else:
                self._log(f"Failed (code {proc.returncode}): {output}")
                return False, output
        except Exception as e:
            err = str(e)
            self._log(f"Exception: {err}")
            return False, err

    def set_one_time_boot(self, entry: OSEntry) -> Tuple[bool, str]:
        """
        Configures the system to boot into the specified OS once on next restart.
        Handles both UEFI Firmware entries and Windows OSLoader entries.
        """
        ident = entry.identifier
        if not ident:
            return False, "Target entry does not have a valid identifier."

        # Case 1: Firmware Application (Linux, UEFI NVRAM boot entry)
        if entry.entry_type == "firmware_app":
            # Primary UEFI firmware boot sequence command
            cmd1 = ["bcdedit", "/set", "{fwbootmgr}", "bootsequence", ident]
            success, out = self._execute(cmd1)
            if success:
                return True, f"Successfully scheduled one-time boot for '{entry.name}' in UEFI Firmware Boot Manager."

            # Fallback direct bootsequence
            cmd2 = ["bcdedit", "/bootsequence", ident]
            success2, out2 = self._execute(cmd2)
            if success2:
                return True, f"Successfully scheduled one-time boot for '{entry.name}'."
            return False, f"Failed to set UEFI bootsequence: {out}\nFallback error: {out2}"

        # Case 2: Windows OS Loader (dual-boot Windows, VHD, or Windows Boot Manager entry)
        elif entry.entry_type == "osloader":
            cmd = ["bcdedit", "/bootsequence", ident]
            success, out = self._execute(cmd)
            if success:
                return True, f"Successfully scheduled one-time boot for '{entry.name}' in Windows Boot Manager."
            return False, f"Failed to set Windows Boot Loader bootsequence: {out}"

        # Case 3: Other / Hardware / Fallback
        else:
            # Try both fwbootmgr and direct
            cmd_fw = ["bcdedit", "/set", "{fwbootmgr}", "bootsequence", ident]
            success_fw, out_fw = self._execute(cmd_fw)
            if success_fw:
                return True, f"Successfully scheduled one-time boot for '{entry.name}'."

            cmd_direct = ["bcdedit", "/bootsequence", ident]
            success_d, out_d = self._execute(cmd_direct)
            if success_d:
                return True, f"Successfully scheduled one-time boot for '{entry.name}'."

            return False, f"Failed to set bootsequence: {out_fw} / {out_d}"

    def clear_one_time_boot(self) -> Tuple[bool, str]:
        """Clears any pending one-time boot sequence."""
        res1, out1 = self._execute(["bcdedit", "/deletevalue", "{fwbootmgr}", "bootsequence"])
        res2, out2 = self._execute(["bcdedit", "/deletevalue", "{bootmgr}", "bootsequence"])

        if res1 or res2:
            return True, "One-time boot sequence has been cleared. Next reboot will follow standard boot order."
        return False, f"Could not clear boot sequence (it may already be empty): {out1}"

    def set_default_boot(self, entry: OSEntry) -> Tuple[bool, str]:
        """Sets the specified OS as the permanent default boot entry."""
        ident = entry.identifier
        if not ident:
            return False, "Target entry does not have a valid identifier."

        if entry.entry_type == "firmware_app":
            # For UEFI firmware applications, set as default in fwbootmgr and move to front of displayorder
            cmd1 = ["bcdedit", "/set", "{fwbootmgr}", "default", ident]
            cmd2 = ["bcdedit", "/set", "{fwbootmgr}", "displayorder", ident, "/addfirst"]
            s1, o1 = self._execute(cmd1)
            s2, o2 = self._execute(cmd2)
            if s1 or s2:
                return True, f"'{entry.name}' is now set as the permanent default boot entry in UEFI."
            return False, f"Failed to set default: {o1}"

        elif entry.entry_type == "osloader":
            cmd = ["bcdedit", "/default", ident]
            s, o = self._execute(cmd)
            if s:
                return True, f"'{entry.name}' is now set as the default Windows OS."
            return False, f"Failed to set default OS: {o}"

        else:
            cmd = ["bcdedit", "/default", ident]
            s, o = self._execute(cmd)
            return s, o

    def reboot(self, delay_seconds: int = 0) -> Tuple[bool, str]:
        """Initiates a system restart."""
        cmd = ["shutdown", "/r", "/t", str(max(0, delay_seconds)), "/f"]
        return self._execute(cmd)

    def abort_reboot(self) -> Tuple[bool, str]:
        """Aborts a pending timed restart."""
        return self._execute(["shutdown", "/a"])

    def reboot_to_uefi_firmware(self) -> Tuple[bool, str]:
        """Reboots directly into motherboard UEFI BIOS setup interface."""
        # /fw reboots to firmware user interface
        cmd = ["shutdown", "/r", "/fw", "/t", "0", "/f"]
        success, out = self._execute(cmd)
        if not success:
            # Some motherboards require shutdown /r /fw without /f or with /t 1
            cmd2 = ["shutdown", "/r", "/fw", "/t", "1"]
            return self._execute(cmd2)
        return success, out

    def reboot_to_recovery_menu(self) -> Tuple[bool, str]:
        """Reboots into Windows Advanced Recovery Options menu."""
        cmd = ["shutdown", "/r", "/o", "/t", "0", "/f"]
        return self._execute(cmd)
