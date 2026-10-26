"""
Main Application Window for NextBoot.
Integrates detection, card list, action toolbar, elevation status, and reboot workflows.
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List

from core.os_detector import OSDetector, OSEntry
from core.boot_manager import BootManager
from core.bios_manager import BIOSManager
from core.elevation import is_admin, elevate_process
from core.esp_scanner import ESPScanner
from ui.theme import Theme
from ui.os_card import OSCard
from ui.modal_reboot import RebootModal
from ui.modal_bios_settings import BIOSSettingsModal
from ui.modal_bios_updater import BIOSUpdaterModal
from ui.log_window import LogWindow

class AppWindow(tk.Tk):
    """Main window for NextBoot OS Switcher."""

    def __init__(self, simulate_mode: bool = False):
        super().__init__()
        self.simulate_mode = simulate_mode
        self.is_elevated = is_admin()

        self.title("NextBoot — Multi-OS Boot Manager")
        self.geometry("900x700")
        self.minsize(760, 560)
        self.configure(bg=Theme.BG_ROOT)

        # Center on screen
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w, h = 900, 700
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        # Core engines
        self.detector = OSDetector()
        self.boot_manager = BootManager(simulate=self.simulate_mode)
        self.bios_manager = BIOSManager(simulate=self.simulate_mode)
        self.esp_scanner = ESPScanner()

        self.entries: List[OSEntry] = []
        self.show_hardware_entries = tk.BooleanVar(value=False)
        self.raw_bcd_cache = ""

        self._build_ui()
        self.refresh_entries()

    def _build_ui(self):
        # 1. Top Header
        self._build_header()

        # 2. Elevation Warning Banner (if running unprivileged)
        if not self.is_elevated and not self.simulate_mode:
            self._build_elevation_banner()

        # 3. Quick Action Toolbar
        self._build_toolbar()

        # 4. Scrollable OS List Container
        self._build_os_list_container()

        # 5. Bottom Status Footer
        self._build_footer()

    def _build_header(self):
        header = tk.Frame(self, bg=Theme.BG_HEADER, padx=24, pady=16)
        header.pack(fill="x")

        # Left Title
        title_box = tk.Frame(header, bg=Theme.BG_HEADER)
        title_box.pack(side="left")

        app_title = tk.Label(
            title_box,
            text="NextBoot",
            font=Theme.FONT_TITLE,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_HEADER
        )
        app_title.pack(anchor="w")

        app_subtitle = tk.Label(
            title_box,
            text="Select an operating system to boot directly on next restart",
            font=Theme.FONT_SUBTITLE,
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_HEADER
        )
        app_subtitle.pack(anchor="w", pady=(2, 0))

        # Right Status Badges
        chips_box = tk.Frame(header, bg=Theme.BG_HEADER)
        chips_box.pack(side="right")

        # Admin status badge
        if self.is_elevated:
            admin_text = "🛡️ Administrator"
            admin_bg = Theme.BADGE_CURRENT_BG
            admin_fg = Theme.BADGE_CURRENT_FG
        else:
            admin_text = "⚠️ Standard User"
            admin_bg = Theme.BADGE_NEXT_BG
            admin_fg = Theme.BADGE_NEXT_FG

        chip_admin = tk.Label(
            chips_box,
            text=admin_text,
            font=Theme.FONT_BADGE,
            bg=admin_bg,
            fg=admin_fg,
            padx=8,
            pady=3
        )
        chip_admin.pack(side="left", padx=4)

        # UEFI status badge
        uefi_text = "⚡ UEFI Mode" if self.detector.is_uefi else "Legacy BIOS"
        chip_uefi = tk.Label(
            chips_box,
            text=uefi_text,
            font=Theme.FONT_BADGE,
            bg=Theme.BADGE_DEFAULT_BG,
            fg=Theme.BADGE_DEFAULT_FG,
            padx=8,
            pady=3
        )
        chip_uefi.pack(side="left", padx=4)

    def _build_elevation_banner(self):
        self.banner = tk.Frame(self, bg="#451a03", padx=20, pady=10) # Amber-900
        self.banner.pack(fill="x")

        lbl = tk.Label(
            self.banner,
            text="⚠️ Running in read-only mode. Administrator privileges are required to configure UEFI and BCD boot targets.",
            font=Theme.FONT_SUBTITLE,
            fg="#fef3c7",
            bg="#451a03"
        )
        lbl.pack(side="left")

        btn_elevate = tk.Button(
            self.banner,
            text="🛡️ Elevate Now",
            font=Theme.FONT_BTN_SM,
            bg=Theme.BTN_PRIMARY_BG,
            fg=Theme.BTN_PRIMARY_FG,
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._on_elevate_clicked
        )
        btn_elevate.pack(side="right")

    def _build_toolbar(self):
        toolbar = tk.Frame(self, bg=Theme.BG_ROOT, padx=24, pady=12)
        toolbar.pack(fill="x")

        # Refresh Button
        self.btn_refresh = tk.Button(
            toolbar,
            text="🔄 Refresh",
            font=Theme.FONT_BTN_SM,
            bg=Theme.BTN_SECONDARY_BG,
            fg=Theme.BTN_SECONDARY_FG,
            activebackground=Theme.BTN_SECONDARY_HOVER,
            activeforeground=Theme.BTN_SECONDARY_FG,
            bd=0,
            padx=10,
            pady=6,
            cursor="hand2",
            command=self.refresh_entries
        )
        self.btn_refresh.pack(side="left", padx=(0, 6))

        # Firmware & Dual-Boot Settings Button
        btn_bios_settings = tk.Button(
            toolbar,
            text="⚙️ BIOS & Dual-Boot Settings",
            font=Theme.FONT_BTN_SM,
            bg=Theme.BTN_PRIMARY_BG,
            fg=Theme.BTN_PRIMARY_FG,
            activebackground=Theme.BTN_PRIMARY_HOVER,
            activeforeground=Theme.BTN_PRIMARY_FG,
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._on_open_bios_settings
        )
        btn_bios_settings.pack(side="left", padx=(0, 6))

        # Universal BIOS Update Assistant Button
        btn_bios_updater = tk.Button(
            toolbar,
            text="⚡ BIOS Update Assistant",
            font=Theme.FONT_BTN_SM,
            bg=Theme.BTN_SUCCESS_BG,
            fg=Theme.BTN_SUCCESS_FG,
            activebackground=Theme.BTN_SUCCESS_HOVER,
            activeforeground=Theme.BTN_SUCCESS_FG,
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._on_open_bios_updater
        )
        btn_bios_updater.pack(side="left", padx=(0, 6))

        # Reboot to BIOS Button
        btn_bios = tk.Button(
            toolbar,
            text="⚡ Reboot to BIOS",
            font=Theme.FONT_BTN_SM,
            bg=Theme.BTN_SECONDARY_BG,
            fg=Theme.BTN_SECONDARY_FG,
            activebackground=Theme.BTN_SECONDARY_HOVER,
            activeforeground=Theme.BTN_SECONDARY_FG,
            bd=0,
            padx=10,
            pady=6,
            cursor="hand2",
            command=self._on_reboot_to_bios
        )
        btn_bios.pack(side="left", padx=(0, 6))

        # Windows Recovery Menu Button
        btn_recovery = tk.Button(
            toolbar,
            text="🛠️ Recovery Menu",
            font=Theme.FONT_BTN_SM,
            bg=Theme.BTN_SECONDARY_BG,
            fg=Theme.BTN_SECONDARY_FG,
            activebackground=Theme.BTN_SECONDARY_HOVER,
            activeforeground=Theme.BTN_SECONDARY_FG,
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._on_reboot_to_recovery
        )
        btn_recovery.pack(side="left", padx=(0, 8))

        # Clear Queued Boot
        btn_clear = tk.Button(
            toolbar,
            text="🧹 Clear Queued Boot",
            font=Theme.FONT_BTN_SM,
            bg=Theme.BTN_SECONDARY_BG,
            fg=Theme.BTN_SECONDARY_FG,
            activebackground=Theme.BTN_SECONDARY_HOVER,
            activeforeground=Theme.BTN_SECONDARY_FG,
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._on_clear_queued
        )
        btn_clear.pack(side="left", padx=(0, 8))

        # Deep Scan ESP
        btn_esp = tk.Button(
            toolbar,
            text="🔍 Deep Scan ESP",
            font=Theme.FONT_BTN_SM,
            bg=Theme.BTN_SECONDARY_BG,
            fg=Theme.BTN_SECONDARY_FG,
            activebackground=Theme.BTN_SECONDARY_HOVER,
            activeforeground=Theme.BTN_SECONDARY_FG,
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._on_scan_esp
        )
        btn_esp.pack(side="left", padx=(0, 8))

        # Diagnostics / Logs (Right aligned)
        btn_logs = tk.Button(
            toolbar,
            text="📜 Logs",
            font=Theme.FONT_BTN_SM,
            bg=Theme.BTN_SECONDARY_BG,
            fg=Theme.BTN_SECONDARY_FG,
            activebackground=Theme.BTN_SECONDARY_HOVER,
            activeforeground=Theme.BTN_SECONDARY_FG,
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._on_view_logs
        )
        btn_logs.pack(side="right")

        # Hardware entries checkbox
        chk_hw = tk.Checkbutton(
            toolbar,
            text="Show Hardware Devices",
            variable=self.show_hardware_entries,
            font=Theme.FONT_SUBTITLE,
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_ROOT,
            activebackground=Theme.BG_ROOT,
            activeforeground=Theme.TEXT_PRIMARY,
            selectcolor=Theme.BG_INPUT,
            command=self._render_cards
        )
        chk_hw.pack(side="right", padx=(0, 12))

    def _build_os_list_container(self):
        container = tk.Frame(self, bg=Theme.BG_ROOT, padx=24)
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(container, bg=Theme.BG_ROOT, bd=0, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview, bg=Theme.BG_CARD)

        self.scrollable_frame = tk.Frame(self.canvas, bg=Theme.BG_ROOT)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_frame_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(xscrollcommand=None, yscrollcommand=self.scrollbar.set)

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Mouse wheel binding
        self.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_frame_window, width=event.width)

    def _on_mousewheel(self, event):
        if self.canvas.winfo_exists():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _build_footer(self):
        footer = tk.Frame(self, bg=Theme.BG_HEADER, padx=24, pady=8)
        footer.pack(fill="x", side="bottom")

        self.footer_status = tk.Label(
            footer,
            text="Ready. Select an OS card and click 'Boot into this OS'.",
            font=Theme.FONT_SUBTITLE,
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_HEADER
        )
        self.footer_status.pack(side="left")

        safety_note = tk.Label(
            footer,
            text="Safe & Non-Destructive One-Time Boot • v1.0.0",
            font=Theme.FONT_BADGE,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_HEADER
        )
        safety_note.pack(side="right")

    def refresh_entries(self):
        """Discovers OS entries and updates the UI."""
        self.footer_status.configure(text="Scanning BCD and UEFI boot entries...", fg=Theme.TEXT_PRIMARY)
        self.update_idletasks()

        # In simulation mode or unprivileged demo mode
        self.entries = self.detector.detect_all(simulate_if_unprivileged=True)
        self.raw_bcd_cache = (
            self.detector.run_bcdedit(["/enum", "firmware"]) + "\n" +
            self.detector.run_bcdedit(["/enum", "osloader"])
        )

        self._render_cards()
        count_os = sum(1 for e in self.entries if e.os_family != "hardware")
        self.footer_status.configure(
            text=f"Scan complete. Found {count_os} operating system(s).",
            fg=Theme.TEXT_SECONDARY
        )

    def _render_cards(self):
        """Draws the OS cards inside the scrollable container."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        visible_entries = [
            e for e in self.entries
            if self.show_hardware_entries.get() or e.os_family != "hardware"
        ]

        if not visible_entries:
            empty_frame = tk.Frame(self.scrollable_frame, bg=Theme.BG_CARD, padx=30, pady=30, highlightthickness=1, highlightbackground=Theme.BORDER_DEFAULT)
            empty_frame.pack(fill="x", pady=20)

            tk.Label(
                empty_frame,
                text="No Operating Systems Detected",
                font=Theme.FONT_TITLE,
                fg=Theme.TEXT_PRIMARY,
                bg=Theme.BG_CARD
            ).pack(pady=(0, 6))

            hint_text = (
                "NextBoot could not read any UEFI or Windows boot entries.\n"
                "• If you have not elevated yet, click 'Elevate Now' above to grant Administrator access.\n"
                "• If your second OS was installed without an NVRAM entry, click 'Deep Scan ESP' in the toolbar."
            )
            tk.Label(
                empty_frame,
                text=hint_text,
                font=Theme.FONT_SUBTITLE,
                fg=Theme.TEXT_SECONDARY,
                bg=Theme.BG_CARD,
                justify="center"
            ).pack()
            return

        # Render each OS card
        for entry in visible_entries:
            card = OSCard(
                self.scrollable_frame,
                entry=entry,
                on_boot_clicked=self._on_boot_card_clicked,
                on_default_clicked=self._on_default_card_clicked
            )
            card.pack(fill="x", pady=6)

    def _on_boot_card_clicked(self, entry: OSEntry):
        """Opens the reboot modal for the selected OS."""
        modal = RebootModal(
            self,
            entry=entry,
            boot_manager=self.boot_manager,
            on_success_callback=lambda e: self.refresh_entries()
        )

    def _on_default_card_clicked(self, entry: OSEntry):
        """Sets the selected OS as the permanent default boot target."""
        confirm = messagebox.askyesno(
            "Confirm Default OS",
            f"Set '{entry.name}' as the permanent default operating system for this computer?\n\n"
            "This will change the boot priority order so that normal boots default to this OS.",
            parent=self
        )
        if confirm:
            success, msg = self.boot_manager.set_default_boot(entry)
            if success:
                messagebox.showinfo("Default OS Updated", msg, parent=self)
                self.refresh_entries()
            else:
                messagebox.showerror("Error", f"Failed to set default: {msg}", parent=self)

    def _on_clear_queued(self):
        """Clears any pending one-time boot sequence."""
        success, msg = self.boot_manager.clear_one_time_boot()
        if success:
            messagebox.showinfo("Boot Sequence Cleared", msg, parent=self)
            self.refresh_entries()
        else:
            messagebox.showwarning("Notice", msg, parent=self)

    def _on_open_bios_settings(self):
        """Opens Motherboard Firmware & Dual-Boot Settings modal."""
        BIOSSettingsModal(
            self,
            entries=self.entries,
            bios_manager=self.bios_manager,
            on_order_saved_callback=self.refresh_entries
        )

    def _on_open_bios_updater(self):
        """Opens Universal BIOS Update Assistant."""
        BIOSUpdaterModal(self)

    def _on_reboot_to_bios(self):
        """Reboots system into motherboard UEFI BIOS setup."""
        confirm = messagebox.askyesno(
            "Reboot to BIOS / UEFI Setup",
            "Are you sure you want to restart your computer directly into the UEFI BIOS Setup screen now?",
            parent=self
        )
        if confirm:
            success, msg = self.boot_manager.reboot_to_uefi_firmware()
            if not success:
                messagebox.showerror("Error", f"Failed to schedule reboot to BIOS: {msg}", parent=self)

    def _on_reboot_to_recovery(self):
        """Reboots system into Windows Recovery Options."""
        confirm = messagebox.askyesno(
            "Reboot to Windows Recovery",
            "Restart into Windows Advanced Startup / Recovery Menu?",
            parent=self
        )
        if confirm:
            success, msg = self.boot_manager.reboot_to_recovery_menu()
            if not success:
                messagebox.showerror("Error", f"Failed to trigger recovery reboot: {msg}", parent=self)

    def _on_scan_esp(self):
        """Performs a deep scan of the EFI system partition for installed bootloaders."""
        self.footer_status.configure(text="Mounting and inspecting EFI partition...", fg=Theme.TEXT_PRIMARY)
        self.update_idletasks()

        loaders = self.esp_scanner.scan_esp()
        if not loaders:
            messagebox.showinfo(
                "ESP Deep Scan",
                "Deep scan completed. No unregistered EFI loaders found, or Administrator access is required to mount the ESP partition.",
                parent=self
            )
        else:
            lines = [f"• {l.suggested_name} ({l.file_path})" for l in loaders]
            msg = (
                f"Found {len(loaders)} bootloader file(s) on the EFI partition:\n\n" +
                "\n".join(lines)
            )
            messagebox.showinfo("ESP Deep Scan Results", msg, parent=self)

        self.footer_status.configure(text="Ready.", fg=Theme.TEXT_SECONDARY)

    def _on_view_logs(self):
        """Opens diagnostics log viewer."""
        LogWindow(self, self.boot_manager.log_history, self.raw_bcd_cache)

    def _on_elevate_clicked(self):
        """Relaunches application with UAC elevation."""
        if elevate_process():
            self.destroy()
            sys.exit(0)
        else:
            messagebox.showerror(
                "Elevation Denied",
                "Administrator privileges were not granted. NextBoot will remain in standard view mode.",
                parent=self
            )
