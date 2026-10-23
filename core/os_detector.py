"""
OS Detector module for NextBoot.
Parses Windows BCD store and UEFI firmware NVRAM boot entries to discover all installed operating systems.
"""

import os
import re
import subprocess
from typing import List, Dict, Any, Optional

class OSEntry:
    """Represents a detected operating system or boot target."""
    def __init__(self,
                 identifier: str,
                 name: str,
                 entry_type: str, # 'firmware_app', 'osloader', 'bootmgr', 'hardware', 'esp_file'
                 path: str = "",
                 device: str = "",
                 os_family: str = "generic",
                 is_current: bool = False,
                 is_default: bool = False,
                 is_next_boot: bool = False,
                 raw_data: Optional[Dict[str, Any]] = None):
        self.identifier = identifier
        self.name = name
        self.entry_type = entry_type
        self.path = path
        self.device = device
        self.os_family = os_family  # windows, ubuntu, fedora, arch, debian, mint, etc.
        self.is_current = is_current
        self.is_default = is_default
        self.is_next_boot = is_next_boot
        self.raw_data = raw_data or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identifier": self.identifier,
            "name": self.name,
            "entry_type": self.entry_type,
            "path": self.path,
            "device": self.device,
            "os_family": self.os_family,
            "is_current": self.is_current,
            "is_default": self.is_default,
            "is_next_boot": self.is_next_boot,
        }

    def __repr__(self) -> str:
        flags = []
        if self.is_current: flags.append("CURRENT")
        if self.is_default: flags.append("DEFAULT")
        if self.is_next_boot: flags.append("NEXT_BOOT")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        return f"<OSEntry {self.name} ({self.os_family}) {self.identifier}{flag_str}>"


class OSDetector:
    """Discovers and parses all installed OS boot entries on Windows."""

    # Distro / OS classification rules (matching against description & path)
    DISTRO_RULES = [
        ("ubuntu", [r"ubuntu", r"shimx64\.efi.*ubuntu", r"grubx64\.efi.*ubuntu"]),
        ("fedora", [r"fedora", r"shimx64\.efi.*fedora"]),
        ("debian", [r"debian"]),
        ("arch", [r"arch\s*linux", r"arch", r"endeavour", r"garuda"]),
        ("mint", [r"linux\s*mint", r"mint"]),
        ("pop_os", [r"pop!_os", r"pop_os", r"system76"]),
        ("manjaro", [r"manjaro"]),
        ("opensuse", [r"opensuse", r"suse"]),
        ("kali", [r"kali"]),
        ("zorin", [r"zorin"]),
        ("elementary", [r"elementary"]),
        ("steamos", [r"steamos", r"holoiso", r"bazzite", r"chimera"]),
        ("redhat", [r"red\s*hat", r"rhel", r"centos", r"almalinux", r"rocky"]),
        ("macos", [r"opencore", r"clover", r"macos", r"mac\s*os", r"hackintosh"]),
        ("freebsd", [r"freebsd", r"openbsd", r"netbsd"]),
        ("android", [r"android", r"bliss", r"primeos", r"chromeos"]),
        ("grub", [r"grub", r"refind", r"systemd-boot", r"linux"]),
        ("windows", [r"windows", r"winload", r"bootmgfw"]),
    ]

    HARDWARE_PATTERNS = [
        r"realtek", r"intel.*boot", r"pcie\s*gbe", r"ipv4", r"ipv6",
        r"network\s*boot", r"pxe", r"cd/dvd", r"hard\s*drive", r"usb",
        r"removable", r"setup", r"diagnostic", r"memdiag"
    ]

    def __init__(self):
        self.last_error = None
        self.firmware_bootsequence = None
        self.bootmgr_bootsequence = None
        self.firmware_default = None
        self.bootmgr_default = None
        self.is_uefi = self._detect_uefi()

    def _detect_uefi(self) -> bool:
        """Checks if current system booted in UEFI mode."""
        try:
            # Check environment or bcdedit output
            system_root = os.environ.get("SystemRoot", r"C:\Windows")
            panther_setup = os.path.join(system_root, "Panther", "setupact.log")
            if os.path.exists(panther_setup):
                with open(panther_setup, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if "Callback_BootEnvironmentDetect: Detected boot environment: EFI" in line:
                            return True
                        if "Callback_BootEnvironmentDetect: Detected boot environment: BIOS" in line:
                            return False
        except Exception:
            pass
        return True # Default assume modern UEFI

    def run_bcdedit(self, args: List[str]) -> str:
        """Executes bcdedit with specified arguments and returns decoded output."""
        cmd = ["bcdedit"] + args
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            if proc.returncode != 0:
                err = proc.stderr.strip() or proc.stdout.strip()
                self.last_error = f"bcdedit error (code {proc.returncode}): {err}"
                return ""
            return proc.stdout
        except FileNotFoundError:
            self.last_error = "bcdedit executable not found."
            return ""
        except Exception as e:
            self.last_error = str(e)
            return ""

    def parse_raw_bcd_blocks(self, text: str) -> List[Dict[str, Any]]:
        """Parses bcdedit tabular output into structured dictionaries."""
        entries = []
        current_entry = {}
        current_header = ""
        current_key = None

        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            # Separator lines like "-------------------"
            if re.match(r'^-{3,}$', stripped):
                continue

            # Match standard "key               value"
            kv_match = re.match(r'^([a-zA-Z0-9_\-\.\(\)\s]+?)\s{2,}(.+)$', line)
            continuation_match = re.match(r'^\s{10,}(.+)$', line)

            if kv_match:
                key = kv_match.group(1).strip().lower()
                val = kv_match.group(2).strip()

                if key == 'identifier':
                    if current_entry.get('identifier'):
                        entries.append(current_entry)
                        current_entry = {}
                    current_entry['header'] = current_header
                    current_entry['identifier'] = val
                    current_key = 'identifier'
                else:
                    current_entry[key] = val
                    current_key = key
            elif continuation_match and current_key:
                val = continuation_match.group(1).strip()
                existing = current_entry.get(current_key, '')
                if isinstance(existing, list):
                    existing.append(val)
                elif existing:
                    current_entry[current_key] = [existing, val]
                else:
                    current_entry[current_key] = val
            else:
                current_header = stripped
                current_key = None

        if current_entry.get('identifier'):
            entries.append(current_entry)

        return entries

    def classify_entry(self, entry_dict: Dict[str, Any]) -> OSEntry:
        """Classifies a parsed BCD entry into a typed OSEntry."""
        ident = entry_dict.get("identifier", "").strip()
        header = entry_dict.get("header", "").lower()
        desc = entry_dict.get("description", "").strip()
        path = entry_dict.get("path", "").strip()
        device = entry_dict.get("device", "") or entry_dict.get("osdevice", "")

        # If description is missing, synthesize from header/ident
        if not desc:
            if ident.lower() == "{fwbootmgr}":
                desc = "Firmware Boot Manager"
            elif ident.lower() == "{bootmgr}":
                desc = "Windows Boot Manager"
            elif ident.lower() == "{current}":
                desc = "Current Windows Installation"
            else:
                desc = f"Boot Entry {ident[:8]}"

        # Determine entry category
        if "firmware boot manager" in header or ident.lower() == "{fwbootmgr}":
            entry_type = "firmware_mgr"
        elif "windows boot manager" in header or ident.lower() == "{bootmgr}":
            entry_type = "bootmgr"
        elif "firmware application" in header:
            entry_type = "firmware_app"
        elif "windows boot loader" in header or "osloader" in header:
            entry_type = "osloader"
        else:
            entry_type = "unknown"

        # Check if hardware / network device
        is_hw = False
        full_text = f"{desc} {path} {header}".lower()
        for hw_pat in self.HARDWARE_PATTERNS:
            if re.search(hw_pat, full_text):
                is_hw = True
                break

        if is_hw and entry_type == "firmware_app":
            entry_type = "hardware"

        # Determine OS Family
        os_family = "other"
        if entry_type == "hardware":
            os_family = "hardware"
        elif entry_type == "bootmgr" or entry_type == "firmware_mgr":
            os_family = "bootmgr"
        else:
            for family, patterns in self.DISTRO_RULES:
                matched = False
                for p in patterns:
                    if re.search(p, full_text):
                        os_family = family
                        matched = True
                        break
                if matched:
                    break

        # Check flags: current, default, next boot
        is_current = (ident.lower() == "{current}")
        is_default = False
        is_next_boot = False

        if self.firmware_bootsequence:
            seq = self.firmware_bootsequence
            if isinstance(seq, list) and ident.lower() in [s.lower() for s in seq]:
                is_next_boot = True
            elif isinstance(seq, str) and ident.lower() == seq.lower():
                is_next_boot = True

        if self.bootmgr_bootsequence:
            seq = self.bootmgr_bootsequence
            if isinstance(seq, list) and ident.lower() in [s.lower() for s in seq]:
                is_next_boot = True
            elif isinstance(seq, str) and ident.lower() == seq.lower():
                is_next_boot = True

        if self.firmware_default and ident.lower() == str(self.firmware_default).lower():
            is_default = True
        if self.bootmgr_default and ident.lower() == str(self.bootmgr_default).lower():
            is_default = True

        return OSEntry(
            identifier=ident,
            name=desc,
            entry_type=entry_type,
            path=path,
            device=device,
            os_family=os_family,
            is_current=is_current,
            is_default=is_default,
            is_next_boot=is_next_boot,
            raw_data=entry_dict
        )

    def detect_all(self, simulate_if_unprivileged: bool = False) -> List[OSEntry]:
        """
        Discovers all boot entries by querying firmware and osloader stores.
        Returns a sorted, categorized list of OSEntries.
        """
        self.last_error = None
        firmware_text = self.run_bcdedit(["/enum", "firmware"])
        osloader_text = self.run_bcdedit(["/enum", "osloader"])

        # Also get /v text if needed for full GUID resolution
        verbose_text = ""
        if firmware_text or osloader_text:
            verbose_text = self.run_bcdedit(["/enum", "/v"])

        raw_blocks = []
        if firmware_text:
            raw_blocks.extend(self.parse_raw_bcd_blocks(firmware_text))
        if osloader_text:
            raw_blocks.extend(self.parse_raw_bcd_blocks(osloader_text))

        # Check if we were denied access or have zero entries
        if not raw_blocks:
            if simulate_if_unprivileged:
                return self.get_demo_entries()
            return []

        # Find manager entries to extract global bootsequence and default
        self.firmware_bootsequence = None
        self.bootmgr_bootsequence = None
        self.firmware_default = None
        self.bootmgr_default = None

        for b in raw_blocks:
            ident = b.get("identifier", "").lower()
            if ident == "{fwbootmgr}":
                self.firmware_bootsequence = b.get("bootsequence")
                self.firmware_default = b.get("default")
            elif ident == "{bootmgr}":
                self.bootmgr_bootsequence = b.get("bootsequence")
                self.bootmgr_default = b.get("default")

        # Deduplicate blocks by identifier
        seen_ids = set()
        unique_blocks = []
        for b in raw_blocks:
            ident = b.get("identifier", "").lower()
            if ident and ident not in seen_ids:
                seen_ids.add(ident)
                unique_blocks.append(b)

        # Classify entries
        entries = []
        for b in unique_blocks:
            entry = self.classify_entry(b)
            # Skip the root manager containers themselves from the OS selection list
            if entry.entry_type in ("firmware_mgr", "bootmgr"):
                continue
            entries.append(entry)

        # If current Windows was not marked, find {current} or primary Windows loader
        has_current = any(e.is_current for e in entries)
        if not has_current:
            for e in entries:
                if e.entry_type == "osloader" and e.os_family == "windows":
                    e.is_current = True
                    break

        # Sort entries:
        # 1. Current OS first
        # 2. Other bootable operating systems (Linux, alternative Windows)
        # 3. Hardware / Network / Utility entries at the end
        def sort_key(item: OSEntry):
            if item.is_current:
                return (0, item.name)
            if item.entry_type in ("firmware_app", "osloader") and item.os_family != "hardware":
                return (1, item.name)
            return (2, item.name)

        entries.sort(key=sort_key)
        return entries

    @staticmethod
    def get_demo_entries() -> List[OSEntry]:
        """Provides realistic mock entries when previewing in unprivileged test mode."""
        return [
            OSEntry(
                identifier="{current}",
                name="Windows 11 Pro",
                entry_type="osloader",
                path=r"\Windows\system32\winload.efi",
                device="partition=C:",
                os_family="windows",
                is_current=True,
                is_default=True,
                is_next_boot=False
            ),
            OSEntry(
                identifier="{7a56c42a-a92c-11ee-8261-806e6f6e6963}",
                name="Ubuntu 24.04 LTS",
                entry_type="firmware_app",
                path=r"\EFI\UBUNTU\SHIMX64.EFI",
                device=r"partition=\Device\HarddiskVolume1",
                os_family="ubuntu",
                is_current=False,
                is_default=False,
                is_next_boot=False
            ),
            OSEntry(
                identifier="{7a56c42b-a92c-11ee-8261-806e6f6e6963}",
                name="Fedora Workstation 40",
                entry_type="firmware_app",
                path=r"\EFI\FEDORA\SHIMX64.EFI",
                device=r"partition=\Device\HarddiskVolume1",
                os_family="fedora",
                is_current=False,
                is_default=False,
                is_next_boot=False
            ),
            OSEntry(
                identifier="{7a56c42c-a92c-11ee-8261-806e6f6e6963}",
                name="Arch Linux (GRUB)",
                entry_type="firmware_app",
                path=r"\EFI\ARCH\GRUBX64.EFI",
                device=r"partition=\Device\HarddiskVolume1",
                os_family="arch",
                is_current=False,
                is_default=False,
                is_next_boot=False
            ),
            OSEntry(
                identifier="{7a56c42d-a92c-11ee-8261-806e6f6e6963}",
                name="UEFI: IP4 Realtek PCIe GBE Family Controller",
                entry_type="hardware",
                path="",
                device="",
                os_family="hardware",
                is_current=False,
                is_default=False,
                is_next_boot=False
            ),
        ]
