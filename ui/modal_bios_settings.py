"""
Firmware & BIOS Settings Modal for NextBoot.
Provides a comprehensive interface for motherboard diagnostics, UEFI boot order reordering,
boot timeout tuning, and essential dual-boot tweaks (Fast Startup & RTC UTC sync).
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any

from core.os_detector import OSEntry
from core.bios_manager import BIOSManager
from ui.theme import Theme
from ui.icons import IconRenderer

class BIOSSettingsModal(tk.Toplevel):
    """Firmware configuration and dual-boot optimization modal."""

    def __init__(self, parent, entries: List[OSEntry], bios_manager: BIOSManager, on_order_saved_callback=None):
        super().__init__(parent)
        self.entries = list(entries) # Copy of entries for reordering
        self.bios_manager = bios_manager
        self.on_order_saved_callback = on_order_saved_callback

        self.title("Firmware & Dual-Boot Settings — NextBoot")
        self.geometry("740x660")
        self.minsize(680, 580)
        self.configure(bg=Theme.BG_ROOT)
        self.transient(parent)

        # Center on parent window
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        w, h = 740, 660
        x = px + max(0, (pw - w) // 2)
        y = py + max(0, (ph - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.diag = self.bios_manager.get_firmware_diagnostics()

        self._build_ui()

    def _build_ui(self):
        # 1. Header
        header = tk.Frame(self, bg=Theme.BG_HEADER, padx=20, pady=14)
        header.pack(fill="x")

        tk.Label(
            header,
            text="Motherboard & Dual-Boot Settings",
            font=Theme.FONT_TITLE,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_HEADER
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Configure motherboard boot priority, timeouts, and multi-boot clock/drive synchronization",
            font=Theme.FONT_SUBTITLE,
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_HEADER
        ).pack(anchor="w", pady=(2, 0))

        # Main Scrollable Body
        container = tk.Frame(self, bg=Theme.BG_ROOT)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg=Theme.BG_ROOT, bd=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview, bg=Theme.BG_CARD)

        self.body = tk.Frame(canvas, bg=Theme.BG_ROOT, padx=20, pady=12)
        self.body.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=self.body, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 2. Section: Motherboard Diagnostics Card
        self._build_diag_card()

        # 3. Section: Essential Dual-Boot Tweaks
        self._build_tweaks_section()

        # 4. Section: UEFI Boot Order Manager
        self._build_boot_order_section()

        # 5. Section: Boot Menu Timeout
        self._build_timeout_section()

        # Bottom Action Bar
        self._build_bottom_bar()

    def _build_diag_card(self):
        card = tk.Frame(self.body, bg=Theme.BG_CARD, padx=16, pady=12, highlightthickness=1, highlightbackground=Theme.BORDER_DEFAULT)
        card.pack(fill="x", pady=(0, 12))

        # Header of card
        top_row = tk.Frame(card, bg=Theme.BG_CARD)
        top_row.pack(fill="x", pady=(0, 8))

        tk.Label(
            top_row,
            text="🖥️ Motherboard & Firmware Information",
            font=Theme.FONT_CARD_TITLE,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD
        ).pack(side="left")

        # Secure boot badge
        sb = self.diag.get("secure_boot")
        if sb is True:
            sb_text = "Secure Boot: ENABLED"
            sb_bg = Theme.BADGE_CURRENT_BG
            sb_fg = Theme.BADGE_CURRENT_FG
        elif sb is False:
            sb_text = "Secure Boot: DISABLED"
            sb_bg = Theme.BADGE_NEXT_BG
            sb_fg = Theme.BADGE_NEXT_FG
        else:
            sb_text = "Secure Boot: UNKNOWN"
            sb_bg = Theme.BORDER_DEFAULT
            sb_fg = Theme.TEXT_MUTED

        tk.Label(
            top_row,
            text=sb_text,
            font=Theme.FONT_BADGE,
            bg=sb_bg,
            fg=sb_fg,
            padx=8,
            pady=2
        ).pack(side="right")

        # Details Grid
        details = tk.Frame(card, bg=Theme.BG_CARD)
        details.pack(fill="x")

        # Row 1: Motherboard
        mb_name = f"{self.diag.get('manufacturer', '')} {self.diag.get('product', '')}".strip()
        tk.Label(details, text="Motherboard:", font=Theme.FONT_BTN, fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).grid(row=0, column=0, sticky="w", pady=2)
        tk.Label(details, text=mb_name or "Standard PC Motherboard", font=Theme.FONT_CARD_TITLE, fg=Theme.TEXT_PRIMARY, bg=Theme.BG_CARD).grid(row=0, column=1, sticky="w", padx=(10, 0), pady=2)

        # Row 2: BIOS Version
        bios_info = f"{self.diag.get('bios_version', 'N/A')} (Release Date: {self.diag.get('bios_date', 'N/A')})"
        tk.Label(details, text="BIOS Version:", font=Theme.FONT_BTN, fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).grid(row=1, column=0, sticky="w", pady=2)
        tk.Label(details, text=bios_info, font=Theme.FONT_CARD_SUBTITLE, fg=Theme.TEXT_PRIMARY, bg=Theme.BG_CARD).grid(row=1, column=1, sticky="w", padx=(10, 0), pady=2)

    def _build_tweaks_section(self):
        section = tk.Frame(self.body, bg=Theme.BG_CARD, padx=16, pady=12, highlightthickness=1, highlightbackground=Theme.BORDER_DEFAULT)
        section.pack(fill="x", pady=(0, 12))

        tk.Label(
            section,
            text="⚡ Dual-Boot System Optimizations",
            font=Theme.FONT_CARD_TITLE,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD
        ).pack(anchor="w", pady=(0, 10))

        # Tweak 1: Fast Startup
        row_fast = tk.Frame(section, bg=Theme.BG_CARD)
        row_fast.pack(fill="x", pady=4)

        self.var_fast_startup = tk.BooleanVar(value=self.diag.get("fast_startup", False))
        chk_fast = tk.Checkbutton(
            row_fast,
            text="Disable Windows Fast Startup (Recommended for Linux)",
            variable=self.var_fast_startup,
            font=Theme.FONT_BTN,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD,
            activebackground=Theme.BG_CARD,
            activeforeground=Theme.TEXT_PRIMARY,
            selectcolor=Theme.BG_INPUT,
            command=self._on_toggle_fast_startup
        )
        chk_fast.pack(anchor="w")

        tk.Label(
            row_fast,
            text="   When enabled, Windows locks disk drives into a hibernate cache. Disabling this allows Linux to safely read and write your NTFS partitions without filesystem corruption.",
            font=Theme.FONT_CARD_SUBTITLE,
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CARD,
            justify="left",
            wraplength=640
        ).pack(anchor="w")

        # Tweak 2: Hardware RTC Clock in UTC
        row_rtc = tk.Frame(section, bg=Theme.BG_CARD)
        row_rtc.pack(fill="x", pady=(10, 4))

        self.var_rtc_utc = tk.BooleanVar(value=self.diag.get("rtc_utc", False))
        chk_rtc = tk.Checkbutton(
            row_rtc,
            text="Synchronize Hardware RTC Clock to UTC (RealTimeIsUniversal)",
            variable=self.var_rtc_utc,
            font=Theme.FONT_BTN,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD,
            activebackground=Theme.BG_CARD,
            activeforeground=Theme.TEXT_PRIMARY,
            selectcolor=Theme.BG_INPUT,
            command=self._on_toggle_rtc_utc
        )
        chk_rtc.pack(anchor="w")

        tk.Label(
            row_rtc,
            text="   Linux stores UTC time in the motherboard CMOS clock, while Windows defaults to local time. Enabling this prevents your computer clock from shifting by several hours whenever switching between OSes.",
            font=Theme.FONT_CARD_SUBTITLE,
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CARD,
            justify="left",
            wraplength=640
        ).pack(anchor="w")

    def _build_boot_order_section(self):
        section = tk.Frame(self.body, bg=Theme.BG_CARD, padx=16, pady=12, highlightthickness=1, highlightbackground=Theme.BORDER_DEFAULT)
        section.pack(fill="x", pady=(0, 12))

        tk.Label(
            section,
            text="🔀 Motherboard UEFI Boot Priority Order",
            font=Theme.FONT_CARD_TITLE,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(
            section,
            text="Select an operating system and use the Move buttons to change permanent boot order priority:",
            font=Theme.FONT_CARD_SUBTITLE,
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CARD
        ).pack(anchor="w", pady=(0, 8))

        # Listbox + Buttons container
        list_container = tk.Frame(section, bg=Theme.BG_CARD)
        list_container.pack(fill="x")

        # Listbox
        self.listbox_entries = tk.Listbox(
            list_container,
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_PRIMARY,
            selectbackground=Theme.BTN_PRIMARY_BG,
            selectforeground=Theme.TEXT_ON_ACCENT,
            font=Theme.FONT_BTN,
            bd=0,
            highlightthickness=1,
            highlightbackground=Theme.BORDER_DEFAULT,
            height=6
        )
        self.listbox_entries.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self._populate_listbox()

        # Reorder Buttons
        btn_box = tk.Frame(list_container, bg=Theme.BG_CARD)
        btn_box.pack(side="right", fill="y")

        btn_up = tk.Button(
            btn_box,
            text="▲ Move Up",
            font=Theme.FONT_BTN_SM,
            bg=Theme.BTN_SECONDARY_BG,
            fg=Theme.BTN_SECONDARY_FG,
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._move_entry_up
        )
        btn_up.pack(fill="x", pady=2)

        btn_down = tk.Button(
            btn_box,
            text="▼ Move Down",
            font=Theme.FONT_BTN_SM,
            bg=Theme.BTN_SECONDARY_BG,
            fg=Theme.BTN_SECONDARY_FG,
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._move_entry_down
        )
        btn_down.pack(fill="x", pady=2)

        btn_top = tk.Button(
            btn_box,
            text="⭐ Make #1 Priority",
            font=Theme.FONT_BTN_SM,
            bg=Theme.BTN_SECONDARY_BG,
            fg=Theme.BTN_SECONDARY_FG,
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._make_entry_first
        )
        btn_top.pack(fill="x", pady=2)

        # Save Boot Order Button
        btn_save = tk.Button(
            section,
            text="💾 Save New Boot Order to UEFI NVRAM",
            font=Theme.FONT_BTN,
            bg=Theme.BTN_PRIMARY_BG,
            fg=Theme.BTN_PRIMARY_FG,
            activebackground=Theme.BTN_PRIMARY_HOVER,
            activeforeground=Theme.BTN_PRIMARY_FG,
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
            command=self._save_boot_order
        )
        btn_save.pack(anchor="w", pady=(10, 0))

    def _build_timeout_section(self):
        section = tk.Frame(self.body, bg=Theme.BG_CARD, padx=16, pady=12, highlightthickness=1, highlightbackground=Theme.BORDER_DEFAULT)
        section.pack(fill="x", pady=(0, 10))

        tk.Label(
            section,
            text="⏱️ Boot Menu Timeout",
            font=Theme.FONT_CARD_TITLE,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(
            section,
            text="Number of seconds to display the bootloader menu before auto-launching default OS:",
            font=Theme.FONT_CARD_SUBTITLE,
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CARD
        ).pack(anchor="w", pady=(0, 8))

        row_t = tk.Frame(section, bg=Theme.BG_CARD)
        row_t.pack(fill="x")

        self.spin_timeout = tk.Spinbox(
            row_t,
            from_=0,
            to=60,
            width=6,
            font=Theme.FONT_BTN,
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_PRIMARY,
            bd=1,
            highlightbackground=Theme.BORDER_DEFAULT
        )
        self.spin_timeout.delete(0, "end")
        self.spin_timeout.insert(0, str(self.diag.get("timeout", 30)))
        self.spin_timeout.pack(side="left", padx=(0, 8))

        tk.Label(
            row_t,
            text="seconds (0 = instant boot without menu)",
            font=Theme.FONT_CARD_SUBTITLE,
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CARD
        ).pack(side="left", padx=(0, 14))

        btn_timeout = tk.Button(
            row_t,
            text="Apply Timeout",
            font=Theme.FONT_BTN_SM,
            bg=Theme.BTN_SECONDARY_BG,
            fg=Theme.BTN_SECONDARY_FG,
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._on_apply_timeout
        )
        btn_timeout.pack(side="left")

    def _build_bottom_bar(self):
        bottom = tk.Frame(self, bg=Theme.BG_HEADER, padx=20, pady=12)
        bottom.pack(fill="x", side="bottom")

        # Direct Reboot to BIOS setup
        btn_reboot_bios = tk.Button(
            bottom,
            text="⚙️ Reboot to BIOS Setup Screen",
            font=Theme.FONT_BTN,
            bg=Theme.BADGE_HW_BG,
            fg=Theme.TEXT_PRIMARY,
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=self._on_reboot_bios
        )
        btn_reboot_bios.pack(side="left")

        btn_close = tk.Button(
            bottom,
            text="Done",
            font=Theme.FONT_BTN,
            bg=Theme.BTN_PRIMARY_BG,
            fg=Theme.BTN_PRIMARY_FG,
            bd=0,
            padx=16,
            pady=8,
            cursor="hand2",
            command=self.destroy
        )
        btn_close.pack(side="right")

    def _populate_listbox(self):
        self.listbox_entries.delete(0, "end")
        for idx, entry in enumerate(self.entries, 1):
            tag = " [Default]" if idx == 1 else ""
            self.listbox_entries.insert("end", f"#{idx}  {entry.name}{tag}  ({entry.os_family})")

    def _move_entry_up(self):
        sel = self.listbox_entries.curselection()
        if not sel or sel[0] == 0:
            return
        idx = sel[0]
        self.entries[idx - 1], self.entries[idx] = self.entries[idx], self.entries[idx - 1]
        self._populate_listbox()
        self.listbox_entries.selection_set(idx - 1)

    def _move_entry_down(self):
        sel = self.listbox_entries.curselection()
        if not sel or sel[0] >= len(self.entries) - 1:
            return
        idx = sel[0]
        self.entries[idx + 1], self.entries[idx] = self.entries[idx], self.entries[idx + 1]
        self._populate_listbox()
        self.listbox_entries.selection_set(idx + 1)

    def _make_entry_first(self):
        sel = self.listbox_entries.curselection()
        if not sel or sel[0] == 0:
            return
        idx = sel[0]
        item = self.entries.pop(idx)
        self.entries.insert(0, item)
        self._populate_listbox()
        self.listbox_entries.selection_set(0)

    def _save_boot_order(self):
        guids = [e.identifier for e in self.entries if e.identifier]
        if not guids:
            messagebox.showerror("Error", "No valid boot entry identifiers found.", parent=self)
            return

        success, msg = self.bios_manager.set_uefi_boot_order(guids)
        if success:
            messagebox.showinfo("Boot Order Saved", f"{msg}\n\nPrimary default OS is now: {self.entries[0].name}", parent=self)
            if self.on_order_saved_callback:
                self.on_order_saved_callback()
        else:
            messagebox.showerror("Error", f"Failed to save boot order:\n{msg}", parent=self)

    def _on_apply_timeout(self):
        try:
            val = int(self.spin_timeout.get().strip())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number of seconds.", parent=self)
            return

        success, msg = self.bios_manager.set_boot_timeout(val)
        if success:
            messagebox.showinfo("Timeout Updated", msg, parent=self)
        else:
            messagebox.showerror("Error", msg, parent=self)

    def _on_toggle_fast_startup(self):
        # Note: Checkbox has new state in self.var_fast_startup.get()
        # If checked: user wants to ENABLE fast startup (or disable)
        # Let's check: The checkbox text says "Disable Windows Fast Startup"
        # If checked = user wants it disabled!
        disable = self.var_fast_startup.get()
        # enable = not disable
        success, msg = self.bios_manager.set_fast_startup(not disable)
        if not success:
            messagebox.showerror("Error", msg, parent=self)
            self.var_fast_startup.set(not disable) # Revert

    def _on_toggle_rtc_utc(self):
        enable = self.var_rtc_utc.get()
        success, msg = self.bios_manager.set_rtc_utc(enable)
        if not success:
            messagebox.showerror("Error", msg, parent=self)
            self.var_rtc_utc.set(not enable) # Revert

    def _on_reboot_bios(self):
        confirm = messagebox.askyesno(
            "Reboot to BIOS / UEFI Setup",
            "Are you sure you want to restart your computer directly into the motherboard BIOS setup screen now?",
            parent=self
        )
        if confirm:
            import subprocess
            subprocess.run(["shutdown", "/r", "/fw", "/t", "0", "/f"])
