# NextBoot — Multi-OS Boot Manager for Windows 🚀

**NextBoot** is a modern, lightweight Windows software designed to detect all operating systems installed on your computer (UEFI NVRAM boot entries and Windows Boot Manager loaders) and allow you to **reboot directly into a second OS with a single click**.

---

## ✨ Key Features

- **🔍 Automatic Multi-OS Detection**:
  - Automatically queries the Windows BCD store and UEFI NVRAM firmware boot entries (`bcdedit /enum firmware` and `bcdedit /enum osloader`).
  - Auto-identifies **Linux distributions** (Ubuntu, Fedora, Arch Linux, Debian, Linux Mint, Pop!_OS, Manjaro, openSUSE, Kali, SteamOS, etc.).
  - Auto-identifies **Windows installations** (Windows 11, Windows 10, Windows Server).
  - Auto-identifies **Bootloaders & Hackintosh** (GRUB, systemd-boot, rEFInd, OpenCore, Clover).
- **🛡️ Safe & Non-Destructive (One-Time Boot)**:
  - Uses the official Windows one-time boot sequence mechanism (`bcdedit /set {fwbootmgr} bootsequence` and `bcdedit /bootsequence`).
  - **Your permanent boot order is never ruined**: It boots into the selected OS *once*, and future normal boots safely return to your default system.
- **🎨 Windows 11 Fluent Dark UI**:
  - Crisp, High-DPI resolution-independent vector icons for each operating system brand.
  - Interactive cards displaying status badges: `[Currently Active]`, `[Default Boot]`, and `[Scheduled Next Boot]`.
  - Detailed file paths (`\EFI\UBUNTU\SHIMX64.EFI`) and BCD identifiers.
- **⏱️ Flexible Restart Modes**:
  - **Restart Now**: Immediate safe reboot straight into target OS.
  - **10-Second Countdown**: Gives you time to wrap up with an emergency "Abort Restart" button.
  - **Apply (Restart Later)**: Applies the next-boot sequence so the next time you turn on or restart your PC, it boots into that OS.
- **⚙️ Motherboard Firmware & Dual-Boot Settings**:
  - **Live Diagnostics**: Reads your motherboard model, BIOS version, release date, and Secure Boot status.
  - **UEFI Boot Order Editor**: View and reorder your motherboard's permanent NVRAM boot priority order with Move Up / Move Down buttons.
  - **Boot Menu Timeout**: Configure the bootloader countdown timer (0 to 60 seconds).
  - **Windows Fast Startup Toggle**: 1-click toggle to disable hybrid hibernation, preventing NTFS drive lockouts in Linux.
  - **Hardware RTC Clock Sync (UTC)**: 1-click toggle (`RealTimeIsUniversal=1`) to eliminate the clock jumping back/forth between Linux and Windows.
- **⚡ Built-In Firmware Utilities**:
  - **Reboot to BIOS / UEFI Setup**: 1-click reboot directly into motherboard firmware setup without spamming F2/Del (`shutdown /r /fw`).
  - **Windows Recovery Menu**: 1-click reboot to advanced troubleshooting options (`shutdown /r /o`).
  - **Clear Queued Boot**: Cancel any scheduled one-time boot sequence with one click.
  - **ESP Deep Scan**: Inspects the EFI System Partition to find installed `.efi` bootloaders on disk.
- **⚡ Zero External Dependencies**:
  - Built with pure Python standard library (`tkinter`, `ctypes`, `subprocess`, `re`, `json`).
  - Runs out of the box on Windows without needing `pip install` or compiler tools.

---

## 🚀 How to Run

### Method 1: One-Click Launcher (Recommended)
Double-click **`NextBoot.bat`** in this folder:
- It automatically requests Windows Administrator (UAC) privileges.
- Launches the GUI directly.

### Method 2: Silent Launcher (No CMD Window)
Double-click **`NextBoot.vbs`**:
- Launches NextBoot without any black terminal window flash.

### Method 3: Desktop Shortcut
Run **`create_desktop_shortcut.bat`**:
- Creates a handy shortcut named **"NextBoot - OS Switcher"** on your Windows Desktop.

### Method 4: Command Line
```powershell
# Run GUI
python main.py

# Run in test / simulation mode (safe preview)
python main.py --simulate
```

---

## 💻 CLI Commands (For Shortcuts & Automation)

You can also use NextBoot from the command line, scripts, or Stream Deck buttons to switch OSes without opening the GUI:

```powershell
# List all detected operating systems and their GUIDs
python main.py --list

# View Motherboard, BIOS, Secure Boot, and Dual-Boot Diagnostics
python main.py --firmware-info

# Boot directly into Ubuntu on next restart
python main.py --boot "Ubuntu"

# Boot into a specific OS by exact GUID
python main.py --boot-guid "{fa6c9a30-84c1-11ee-8bb4-806e6f6e6963}"

# Queue next boot without restarting immediately
python main.py --boot "Fedora" --no-reboot

# Reboot straight into Motherboard UEFI BIOS Setup
python main.py --bios

# Clear any pending one-time boot sequence
python main.py --clear
```

---

## 🛠️ Project Structure

```
d:\Antigravity\NextBoot\
├── core\
│   ├── os_detector.py      # BCD & UEFI firmware NVRAM boot entry parser
│   ├── boot_manager.py     # One-time boot sequence & restart dispatcher
│   ├── esp_scanner.py      # EFI System Partition (ESP) scanner
│   └── elevation.py        # Windows UAC elevation promoter
├── ui\
│   ├── theme.py            # Windows 11 Fluent dark palette & typography
│   ├── icons.py            # Resolution-independent vector brand graphics
│   ├── os_card.py          # Interactive OS card component
│   ├── modal_reboot.py     # Confirmation & countdown modal
│   ├── app_window.py       # Main application window & toolbar
│   └── log_window.py       # Live diagnostics and raw BCD tables
├── tests\
│   ├── test_detector.py    # Parser unit tests
│   └── test_comprehensive.py # Full suite unit tests
├── main.py                 # Application entry point (GUI + CLI)
├── NextBoot.bat            # Elevated launcher script
├── NextBoot.vbs            # Silent launcher (no console window)
├── create_desktop_shortcut.bat # Desktop shortcut generator
├── build_exe.bat           # PyInstaller compilation script
└── README.md               # Documentation
```

---

## 📦 Building a Standalone `.exe` (Optional)

If you wish to distribute NextBoot as a standalone portable Windows application without requiring Python:
1. Double-click `build_exe.bat`.
2. It will build a single-file portable executable `NextBoot.exe` right in the project folder with embedded Administrator UAC permissions. You can then copy and run `NextBoot.exe` anywhere without needing Python.

---

## 🔒 Security & Safety Guarantee

NextBoot does **not** patch or overwrite boot sectors, MBR, or partition tables. It utilizes Windows's built-in `bcdedit.exe` subsystem to communicate with your motherboard's UEFI firmware boot manager. When you select an OS, it sets a **temporary one-time boot flag** that the motherboard clears upon boot. If anything fails or you change your mind, your standard Windows boot configuration remains 100% intact.

---

## 👤 Author & Maintainer

* **[Zeusx212](https://github.com/Zeusx212)** — Project Creator & Lead Maintainer

