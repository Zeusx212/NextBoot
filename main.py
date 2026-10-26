"""
NextBoot — Multi-OS Boot Manager for Windows.
Main entry point supporting GUI and CLI automation.
"""

import sys
import os
import argparse
import ctypes

# Ensure current directory or PyInstaller bundle directory is in sys.path
if getattr(sys, 'frozen', False):
    basedir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
else:
    basedir = os.path.dirname(os.path.abspath(__file__))

if basedir not in sys.path:
    sys.path.insert(0, basedir)

from core.elevation import is_admin, elevate_process
from core.os_detector import OSDetector
from core.boot_manager import BootManager
from core.bios_manager import BIOSManager
from core.universal_bios_updater import UniversalBIOSUpdater

def set_high_dpi_aware():
    """Enables crisp High-DPI font rendering on modern Windows screens."""
    try:
        # PROCESS_PER_MONITOR_DPI_AWARE = 2, PROCESS_SYSTEM_DPI_AWARE = 1
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

def run_cli(args):
    """Handles CLI arguments for automation and shortcuts."""
    detector = OSDetector()
    boot_manager = BootManager(simulate=args.simulate)
    bios_manager = BIOSManager(simulate=args.simulate)

    # 0. Firmware & Motherboard Diagnostics
    if args.firmware_info:
        info = bios_manager.get_firmware_diagnostics()
        print("\n=== NextBoot: Motherboard & Firmware Diagnostics ===")
        print(f"Motherboard  : {info.get('manufacturer')} {info.get('product')}")
        print(f"BIOS Version : {info.get('bios_version')} ({info.get('bios_date')})")
        print(f"Secure Boot  : {'ENABLED' if info.get('secure_boot') else 'DISABLED'}")
        print(f"Fast Startup : {'ON (Hybrid Hibernation)' if info.get('fast_startup') else 'OFF (Safe for Dual-Boot)'}")
        print(f"RTC Clock    : {'UTC (RealTimeIsUniversal=1)' if info.get('rtc_utc') else 'Local Time'}")
        print(f"Boot Timeout : {info.get('timeout')} seconds\n")
        sys.exit(0)

    # 0b. Universal BIOS Flash Profile & Guide
    if args.bios_guide:
        updater = UniversalBIOSUpdater(simulate=args.simulate)
        prof = updater.get_vendor_profile()
        hw = updater.detect_hardware()
        print("\n=== NextBoot: Universal BIOS Update Profile ===")
        print(f"Motherboard       : {hw.get('manufacturer')} {hw.get('product')}")
        print(f"Installed BIOS    : {hw.get('bios_version')} ({hw.get('bios_date')})")
        print(f"Vendor Protocol   : {prof.display_name}")
        print(f"Flashing Utility  : {prof.flashing_utility}")
        print(f"Flashback File    : {prof.flashback_filename or 'Standard Filename'}")
        print(f"File System Req   : {prof.recommended_fs}")
        print(f"Entry Shortcut    : {prof.shortcut_hint}")
        print("\nStep-by-step Flashing Instructions:")
        for idx, step in enumerate(prof.instructions, 1):
            print(f"  {idx}. {step}")
        print()
        sys.exit(0)

    # 0c. Analyze Firmware Image File
    if args.analyze_bios:
        updater = UniversalBIOSUpdater(simulate=args.simulate)
        try:
            info = updater.analyze_firmware_file(args.analyze_bios)
            print(f"\n=== NextBoot: Firmware Image Analysis ===")
            print(f"File Name         : {info.file_name}")
            print(f"File Size         : {info.file_size_mb:.2f} MB ({info.file_size:,} bytes)")
            print(f"SPI Flash Size    : {'Valid standard SPI capacity' if info.is_valid_spi_size else 'Non-standard capacity'}")
            print(f"Recognized Format : {info.format_type}")
            print(f"Capsule Header    : {'Present (2048-byte header)' if info.has_capsule_header else 'None / Raw'}")
            print(f"SHA-256 Digest    : {info.sha256}")
            print(f"Board Verified    : {'YES (Model string identified inside binary)' if info.matches_detected_board else 'UNCONFIRMED'}")
            if info.matched_strings:
                print(f"Matched Tokens    : {', '.join(info.matched_strings)}")
            if info.recommended_staged_name:
                print(f"Flashback Target  : {info.recommended_staged_name}")
            if info.warnings:
                print("\nWarnings:")
                for w in info.warnings:
                    print(f"  ⚠️ {w}")
            print()
            sys.exit(0)
        except Exception as e:
            print(f"Error analyzing firmware image: {e}")
            sys.exit(1)

    # 0d. Stage Firmware File to Drive
    if args.stage_bios:
        if not args.target_drive:
            print("Error: --target-drive (e.g. 'E:\\') is required when using --stage-bios.")
            sys.exit(1)
        updater = UniversalBIOSUpdater(simulate=args.simulate)
        print(f"\nStaging firmware '{args.stage_bios}' to '{args.target_drive}'...")
        success, msg, created = updater.stage_firmware(args.stage_bios, args.target_drive, create_flashback_copy=True)
        if success:
            print(f"Success!\n{msg}\n")
            sys.exit(0)
        else:
            print(f"Failed: {msg}\n")
            sys.exit(1)

    # 1. List detected OS entries
    if args.list:
        print("\n=== NextBoot: Detected Operating Systems ===")
        entries = detector.detect_all(simulate_if_unprivileged=True)
        if not entries:
            print("No operating systems found or Administrator access denied.")
            sys.exit(1)

        for idx, e in enumerate(entries, 1):
            flags = []
            if e.is_current: flags.append("[CURRENT]")
            if e.is_default: flags.append("[DEFAULT]")
            if e.is_next_boot: flags.append("[NEXT_BOOT]")
            flag_str = " ".join(flags)
            print(f"{idx}. {e.name} {flag_str}")
            print(f"   Identifier : {e.identifier}")
            print(f"   Type       : {e.entry_type} ({e.os_family})")
            if e.path:
                print(f"   Path       : {e.path}")
            print()
        sys.exit(0)

    # 2. Reboot to BIOS / UEFI
    if args.bios:
        if not is_admin() and not args.simulate:
            print("Administrator privileges required. Attempting elevation...")
            elevate_process()
            sys.exit(0)
        print("Rebooting into UEFI Firmware / BIOS Setup...")
        success, msg = boot_manager.reboot_to_uefi_firmware()
        print(f"Result: {msg}")
        sys.exit(0 if success else 1)

    # 3. Clear one-time boot
    if args.clear:
        if not is_admin() and not args.simulate:
            print("Administrator privileges required. Attempting elevation...")
            elevate_process()
            sys.exit(0)
        print("Clearing queued one-time boot sequence...")
        success, msg = boot_manager.clear_one_time_boot()
        print(f"Result: {msg}")
        sys.exit(0 if success else 1)

    # 4. Boot into specified OS by name or GUID
    target = args.boot or args.boot_guid
    if target:
        if not is_admin() and not args.simulate:
            print("Administrator privileges required. Attempting elevation...")
            elevate_process()
            sys.exit(0)

        entries = detector.detect_all(simulate_if_unprivileged=True)
        matched_entry = None

        if args.boot_guid:
            for e in entries:
                if e.identifier.lower() == args.boot_guid.lower():
                    matched_entry = e
                    break
        else:
            query = args.boot.lower()
            for e in entries:
                if query in e.name.lower() or query in e.os_family.lower():
                    matched_entry = e
                    break

        if not matched_entry:
            print(f"Error: Could not find any boot entry matching '{target}'.")
            print("Use --list to view all detected operating system names and GUIDs.")
            sys.exit(1)

        print(f"Found target: {matched_entry.name} ({matched_entry.identifier})")
        success, msg = boot_manager.set_one_time_boot(matched_entry)
        if not success:
            print(f"Error: {msg}")
            sys.exit(1)

        print(f"Success: {msg}")
        if not args.no_reboot:
            delay = args.delay if args.delay is not None else 0
            print(f"Restarting computer in {delay} seconds...")
            boot_manager.reboot(delay_seconds=delay)
        else:
            print("System will boot into this OS on your next manual restart.")
        sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="NextBoot — Windows Multi-OS Boot Manager")
    parser.add_argument("--list", action="store_true", help="List all detected OS boot entries and exit")
    parser.add_argument("--firmware-info", action="store_true", help="Display motherboard and firmware diagnostics")
    parser.add_argument("--boot", type=str, help="Name or distro of OS to boot into (e.g. 'Ubuntu', 'Windows')")
    parser.add_argument("--boot-guid", type=str, help="Exact GUID identifier of OS to boot into")
    parser.add_argument("--delay", type=int, default=0, help="Seconds delay before rebooting (default: 0)")
    parser.add_argument("--no-reboot", action="store_true", help="Schedule one-time boot but do not restart immediately")
    parser.add_argument("--bios", action="store_true", help="Reboot directly into UEFI BIOS Setup")
    parser.add_argument("--clear", action="store_true", help="Clear any scheduled one-time boot sequence")
    parser.add_argument("--bios-guide", action="store_true", help="Display vendor BIOS flashing instructions and Flashback target naming")
    parser.add_argument("--analyze-bios", type=str, help="Analyze and verify a BIOS firmware image binary file")
    parser.add_argument("--stage-bios", type=str, help="Stage a BIOS firmware image file to target drive")
    parser.add_argument("--target-drive", type=str, help="Target drive letter/path for firmware staging (e.g. 'E:\\')")
    parser.add_argument("--simulate", action="store_true", help="Run in simulation / test mode without modifying BCD")
    parser.add_argument("--no-auto-elevate", action="store_true", help="Do not prompt for UAC elevation on launch")

    args = parser.parse_args()

    # If any CLI action was requested, run in CLI mode
    if (args.list or args.firmware_info or args.bios_guide or args.analyze_bios or
        args.stage_bios or args.boot or args.boot_guid or args.bios or args.clear):
        run_cli(args)
        return

    # Check for elevation in GUI mode
    # If not admin and auto-elevation not suppressed, request elevation once
    if not is_admin() and not args.no_auto_elevate and "--elevated-child" not in sys.argv:
        # Prompt UAC runas
        if elevate_process(["--elevated-child"] + sys.argv[1:]):
            sys.exit(0)

    # Start GUI
    set_high_dpi_aware()
    from ui.app_window import AppWindow
    app = AppWindow(simulate_mode=args.simulate)
    app.mainloop()

if __name__ == "__main__":
    main()
