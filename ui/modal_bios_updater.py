"""
Universal BIOS Update Assistant Modal for NextBoot.
Provides a modern Fluent dark-themed interface for analyzing motherboard firmware files,
staging Flashback recovery files to FAT32 USB drives, verifying SHA-256 integrity,
and rebooting directly into the native UEFI BIOS flashing interface.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Optional

from core.universal_bios_updater import UniversalBIOSUpdater, VendorProfile, BIOSImageInfo, StorageTarget
from ui.theme import Theme

class BIOSUpdaterModal(tk.Toplevel):
    """Interactive assistant for multi-vendor BIOS analysis and safe staging."""

    def __init__(self, parent, updater: Optional[UniversalBIOSUpdater] = None):
        super().__init__(parent)
        self.updater = updater or UniversalBIOSUpdater()
        self.vendor_prof = self.updater.get_vendor_profile()
        self.hw_info = self.updater.detect_hardware()

        self.title("Universal BIOS Update Assistant — NextBoot")
        self.geometry("780x720")
        self.minsize(720, 600)
        self.configure(bg=Theme.BG_ROOT)
        self.transient(parent)

        # Center on parent window
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        w, h = 780, 720
        x = px + max(0, (pw - w) // 2)
        y = py + max(0, (ph - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.selected_file_path: Optional[str] = None
        self.image_info: Optional[BIOSImageInfo] = None
        self.storage_targets: List[StorageTarget] = []
        self.create_flashback_var = tk.BooleanVar(value=True if self.vendor_prof.flashback_filename else False)

        self._build_ui()
        self._load_storage_targets()

    def _build_ui(self):
        # 1. Top Header
        header = tk.Frame(self, bg=Theme.BG_HEADER, padx=22, pady=16)
        header.pack(fill="x")

        title_row = tk.Frame(header, bg=Theme.BG_HEADER)
        title_row.pack(fill="x")

        tk.Label(
            title_row,
            text="⚡ Universal BIOS Update Assistant",
            font=Theme.FONT_TITLE,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_HEADER
        ).pack(side="left")

        # Vendor badge
        badge = tk.Label(
            title_row,
            text=f" {self.vendor_prof.display_name} ",
            font=Theme.FONT_BADGE,
            bg=self.vendor_prof.badge_color,
            fg="#ffffff",
            padx=6,
            pady=2
        )
        badge.pack(side="right")

        tk.Label(
            header,
            text="Universal firmware integrity verification, FAT32 Flashback staging, and safe 1-click flasher reboot",
            font=Theme.FONT_SUBTITLE,
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_HEADER
        ).pack(anchor="w", pady=(4, 0))

        # Main Scrollable Body
        container = tk.Frame(self, bg=Theme.BG_ROOT)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg=Theme.BG_ROOT, bd=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview, bg=Theme.BG_CARD)

        self.body = tk.Frame(canvas, bg=Theme.BG_ROOT, padx=22, pady=14)
        self.body.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=self.body, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Section 1: Detected Motherboard & Installed BIOS
        self._build_hardware_card()

        # Section 2: Step 1 - Select & Inspect Firmware File
        self._build_file_picker_section()

        # Section 3: Step 2 - Storage Destination & Flashback Staging
        self._build_staging_section()

        # Section 4: Step-by-Step Vendor Instructions Card
        self._build_instructions_card()

        # Bottom Action Bar
        self._build_bottom_bar()

    def _build_hardware_card(self):
        card = tk.Frame(self.body, bg=Theme.BG_CARD, bd=1, relief="solid", highlightthickness=0, padx=16, pady=12)
        card.pack(fill="x", pady=(0, 14))

        tk.Label(
            card,
            text="CURRENT HARDWARE & INSTALLED FIRMWARE",
            font=("Segoe UI", 9, "bold"),
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CARD
        ).pack(anchor="w", pady=(0, 8))

        grid = tk.Frame(card, bg=Theme.BG_CARD)
        grid.pack(fill="x")

        # Column 1: Motherboard
        c1 = tk.Frame(grid, bg=Theme.BG_CARD)
        c1.pack(side="left", expand=True, fill="x")
        tk.Label(c1, text="Motherboard", font=("Segoe UI", 9), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(anchor="w")
        tk.Label(
            c1,
            text=f"{self.hw_info.get('manufacturer')} {self.hw_info.get('product')}",
            font=("Segoe UI", 11, "bold"),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD
        ).pack(anchor="w")

        # Column 2: Installed BIOS
        c2 = tk.Frame(grid, bg=Theme.BG_CARD)
        c2.pack(side="left", expand=True, fill="x")
        tk.Label(c2, text="Current BIOS Version", font=("Segoe UI", 9), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(anchor="w")
        tk.Label(
            c2,
            text=f"{self.hw_info.get('bios_version')} ({self.hw_info.get('bios_date')})",
            font=("Segoe UI", 11, "bold"),
            fg="#38bdf8",
            bg=Theme.BG_CARD
        ).pack(anchor="w")

        # Column 3: Native Flashing Utility
        c3 = tk.Frame(grid, bg=Theme.BG_CARD)
        c3.pack(side="left", expand=True, fill="x")
        tk.Label(c3, text="Flashing Technology", font=("Segoe UI", 9), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(anchor="w")
        tk.Label(
            c3,
            text=self.vendor_prof.flashing_utility,
            font=("Segoe UI", 10, "bold"),
            fg="#4ade80",
            bg=Theme.BG_CARD
        ).pack(anchor="w")

    def _build_file_picker_section(self):
        frame = tk.LabelFrame(
            self.body,
            text=" STEP 1: SELECT & VERIFY FIRMWARE IMAGE ",
            font=("Segoe UI", 10, "bold"),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_ROOT,
            padx=14,
            pady=12
        )
        frame.pack(fill="x", pady=(0, 14))

        picker_row = tk.Frame(frame, bg=Theme.BG_ROOT)
        picker_row.pack(fill="x", pady=(0, 8))

        self.file_entry = tk.Entry(
            picker_row,
            font=("Segoe UI", 10),
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_PRIMARY,
            insertbackground=Theme.TEXT_PRIMARY,
            relief="flat",
            bd=5
        )
        self.file_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_browse = tk.Button(
            picker_row,
            text="📂 Browse File...",
            font=Theme.FONT_BTN_SM,
            bg=Theme.BTN_PRIMARY_BG,
            fg=Theme.BTN_PRIMARY_FG,
            activebackground=Theme.BTN_PRIMARY_HOVER,
            activeforeground=Theme.BTN_PRIMARY_FG,
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._on_browse_file
        )
        btn_browse.pack(side="right")

        # Dynamic Analysis Result Card
        self.analysis_card = tk.Frame(frame, bg=Theme.BG_CARD, padx=14, pady=10, relief="solid", bd=1)
        self.analysis_card.pack(fill="x")
        self.analysis_card.pack_forget() # Initially hidden until file is chosen

        self.lbl_analysis_title = tk.Label(
            self.analysis_card,
            text="",
            font=("Segoe UI", 10, "bold"),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD
        )
        self.lbl_analysis_title.pack(anchor="w")

        self.lbl_analysis_details = tk.Label(
            self.analysis_card,
            text="",
            font=("Consolas", 9),
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CARD,
            justify="left"
        )
        self.lbl_analysis_details.pack(anchor="w", pady=(4, 4))

        self.lbl_analysis_status = tk.Label(
            self.analysis_card,
            text="",
            font=("Segoe UI", 9, "bold"),
            fg="#4ade80",
            bg=Theme.BG_CARD
        )
        self.lbl_analysis_status.pack(anchor="w")

    def _build_staging_section(self):
        frame = tk.LabelFrame(
            self.body,
            text=" STEP 2: CHOOSE TARGET STORAGE & FLASHBACK PREPARATION ",
            font=("Segoe UI", 10, "bold"),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_ROOT,
            padx=14,
            pady=12
        )
        frame.pack(fill="x", pady=(0, 14))

        tk.Label(
            frame,
            text="Select destination drive (FAT32 USB Flash Drive is strictly required by motherboard firmware):",
            font=Theme.FONT_SUBTITLE,
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_ROOT
        ).pack(anchor="w", pady=(0, 6))

        drive_row = tk.Frame(frame, bg=Theme.BG_ROOT)
        drive_row.pack(fill="x", pady=(0, 8))

        self.drive_combo = ttk.Combobox(drive_row, font=("Segoe UI", 10), state="readonly")
        self.drive_combo.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_refresh_drives = tk.Button(
            drive_row,
            text="🔄 Refresh Drives",
            font=Theme.FONT_BTN_SM,
            bg=Theme.BTN_SECONDARY_BG,
            fg=Theme.BTN_SECONDARY_FG,
            activebackground=Theme.BTN_SECONDARY_HOVER,
            activeforeground=Theme.BTN_SECONDARY_FG,
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self._load_storage_targets
        )
        btn_refresh_drives.pack(side="right")

        # Flashback Option Checkbox
        if self.vendor_prof.flashback_filename:
            fb_text = f"Auto-create standardized Flashback recovery copy ('{self.vendor_prof.flashback_filename}') on drive root"
            chk_fb = tk.Checkbutton(
                frame,
                text=fb_text,
                variable=self.create_flashback_var,
                font=("Segoe UI", 9, "bold"),
                fg=Theme.TEXT_PRIMARY,
                bg=Theme.BG_ROOT,
                activebackground=Theme.BG_ROOT,
                activeforeground=Theme.TEXT_PRIMARY,
                selectcolor=Theme.BG_INPUT
            )
            chk_fb.pack(anchor="w", pady=(2, 6))

        # Staging Action Button & Status
        btn_stage = tk.Button(
            frame,
            text="💾 Stage Firmware File to Selected Drive",
            font=Theme.FONT_BTN_SM,
            bg=Theme.BTN_PRIMARY_BG,
            fg=Theme.BTN_PRIMARY_FG,
            activebackground=Theme.BTN_PRIMARY_HOVER,
            activeforeground=Theme.BTN_PRIMARY_FG,
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=self._on_stage_clicked
        )
        btn_stage.pack(anchor="w", pady=(4, 6))

        self.lbl_stage_status = tk.Label(
            frame,
            text="",
            font=("Segoe UI", 9),
            fg="#4ade80",
            bg=Theme.BG_ROOT,
            justify="left"
        )
        self.lbl_stage_status.pack(anchor="w")

    def _build_instructions_card(self):
        card = tk.LabelFrame(
            self.body,
            text=f" STEP 3: {self.vendor_prof.display_name.upper()} FLASHING WALKTHROUGH ",
            font=("Segoe UI", 10, "bold"),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD,
            padx=14,
            pady=10
        )
        card.pack(fill="x", pady=(0, 10))

        tk.Label(
            card,
            text=f"Shortcut / Entry: {self.vendor_prof.shortcut_hint}",
            font=("Segoe UI", 9, "bold"),
            fg="#38bdf8",
            bg=Theme.BG_CARD
        ).pack(anchor="w", pady=(0, 6))

        for idx, step in enumerate(self.vendor_prof.instructions, 1):
            is_caution = "CAUTION" in step
            fg_color = "#f87171" if is_caution else Theme.TEXT_SECONDARY
            tk.Label(
                card,
                text=f"• {step}",
                font=("Segoe UI", 9, "bold" if is_caution else "normal"),
                fg=fg_color,
                bg=Theme.BG_CARD,
                wraplength=700,
                justify="left"
            ).pack(anchor="w", pady=1)

    def _build_bottom_bar(self):
        bar = tk.Frame(self, bg=Theme.BG_HEADER, padx=22, pady=12)
        bar.pack(fill="x", side="bottom")

        # 1-Click Reboot to Flasher Button (Left aligned, high prominence)
        btn_reboot_flasher = tk.Button(
            bar,
            text="⚡ 1-Click Reboot to BIOS Flasher",
            font=Theme.FONT_BTN_SM,
            bg=Theme.BTN_SUCCESS_BG,
            fg=Theme.BTN_SUCCESS_FG,
            activebackground=Theme.BTN_SUCCESS_HOVER,
            activeforeground=Theme.BTN_SUCCESS_FG,
            bd=0,
            padx=16,
            pady=8,
            cursor="hand2",
            command=self._on_reboot_to_flasher
        )
        btn_reboot_flasher.pack(side="left")

        # Close Button (Right aligned)
        btn_close = tk.Button(
            bar,
            text="Close",
            font=Theme.FONT_BTN_SM,
            bg=Theme.BTN_SECONDARY_BG,
            fg=Theme.BTN_SECONDARY_FG,
            activebackground=Theme.BTN_SECONDARY_HOVER,
            activeforeground=Theme.BTN_SECONDARY_FG,
            bd=0,
            padx=16,
            pady=8,
            cursor="hand2",
            command=self.destroy
        )
        btn_close.pack(side="right")

    def _load_storage_targets(self):
        self.storage_targets = self.updater.get_storage_targets()
        options = [t.display_text for t in self.storage_targets]
        self.drive_combo["values"] = options
        if options:
            self.drive_combo.current(0)

    def _on_browse_file(self):
        initial = os.path.expanduser("~\\Downloads")
        fpath = filedialog.askopenfilename(
            parent=self,
            title="Select Motherboard BIOS Firmware File",
            initialdir=initial if os.path.exists(initial) else "C:\\",
            filetypes=[
                ("BIOS Firmware Files", "*.bin;*.rom;*.cap;*.F*;*.bio;*.exe;*.iso"),
                ("All Files", "*.*")
            ]
        )
        if not fpath:
            return

        self.file_entry.delete(0, tk.END)
        self.file_entry.insert(0, fpath)
        self.selected_file_path = fpath
        self._analyze_file(fpath)

    def _analyze_file(self, fpath: str):
        try:
            self.image_info = self.updater.analyze_firmware_file(fpath)
            self.analysis_card.pack(fill="x", pady=(4, 0))

            info = self.image_info
            size_badge = "Standard SPI Size" if info.is_valid_spi_size else "Non-standard size"

            self.lbl_analysis_title.configure(
                text=f"📦 {info.file_name} — {info.format_type} ({info.file_size_mb:.2f} MB / {size_badge})"
            )

            details_text = f"SHA-256 : {info.sha256}\n"
            if info.matched_strings:
                details_text += f"Verified : Model match '{', '.join(info.matched_strings)}' found inside binary!\n"
            if info.recommended_staged_name:
                details_text += f"Flashback: Standardized name will be '{info.recommended_staged_name}'"

            self.lbl_analysis_details.configure(text=details_text)

            if info.matches_detected_board:
                self.lbl_analysis_status.configure(
                    text="✅ Compatibility Confirmed: Firmware binary directly matches your detected motherboard model!",
                    fg="#4ade80"
                )
            elif info.warnings:
                self.lbl_analysis_status.configure(
                    text=f"⚠️ Notice: {info.warnings[0]}",
                    fg="#fbbf24"
                )
            else:
                self.lbl_analysis_status.configure(
                    text="ℹ️ Ready for staging. Please ensure this file matches your exact motherboard revision.",
                    fg="#38bdf8"
                )

        except Exception as e:
            messagebox.showerror("File Analysis Error", f"Failed to analyze firmware file:\n{e}", parent=self)

    def _on_stage_clicked(self):
        fpath = self.file_entry.get().strip()
        if not fpath or not os.path.isfile(fpath):
            messagebox.showwarning("Select File", "Please select a valid BIOS firmware file first.", parent=self)
            return

        idx = self.drive_combo.current()
        if idx < 0 or idx >= len(self.storage_targets):
            messagebox.showwarning("Select Destination", "Please choose a destination drive from the list.", parent=self)
            return

        target = self.storage_targets[idx]
        if not target.is_fat32:
            proceed = messagebox.askyesno(
                "Non-FAT32 Drive Warning",
                f"Drive {target.letter}: is formatted as {target.fs or 'NTFS/exFAT'}.\n\n"
                "Most motherboards (including Gigabyte Q-Flash and ASUS EZ-Flash) CANNOT read NTFS or exFAT drives during pre-boot flashing!\n\n"
                "Are you sure you want to proceed staging to this drive?",
                parent=self,
                icon="warning"
            )
            if not proceed:
                return

        create_fb = self.create_flashback_var.get()
        success, msg, created = self.updater.stage_firmware(fpath, target.root, create_flashback_copy=create_fb)

        if success:
            file_names = ", ".join(os.path.basename(p) for p in created)
            self.lbl_stage_status.configure(
                text=f"✅ Staging Successful!\nCreated: {file_names} on {target.root}\nIntegrity SHA-256 verified.",
                fg="#4ade80"
            )
            messagebox.showinfo(
                "Firmware Staged Successfully",
                f"Firmware staged to {target.root} successfully!\n\n"
                f"Files created:\n• " + "\n• ".join(created) + "\n\n"
                "Post-copy SHA-256 verification passed with 100% integrity.",
                parent=self
            )
        else:
            self.lbl_stage_status.configure(
                text=f"❌ Staging Failed: {msg}",
                fg="#f87171"
            )
            messagebox.showerror("Staging Failed", msg, parent=self)

    def _on_reboot_to_flasher(self):
        confirm = messagebox.askyesno(
            "Reboot to Motherboard Flasher",
            f"NextBoot will restart your computer directly into the {self.vendor_prof.display_name} UEFI Firmware interface.\n\n"
            f"Shortcut Hint: {self.vendor_prof.shortcut_hint}\n\n"
            "Save all open work in other programs before proceeding.\n\n"
            "Restart now?",
            parent=self,
            icon="question"
        )
        if not confirm:
            return

        success, msg = self.updater.reboot_to_firmware_flasher(delay_seconds=0)
        if not success:
            messagebox.showerror("Reboot Failed", msg, parent=self)
