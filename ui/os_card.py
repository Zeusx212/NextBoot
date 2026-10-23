"""
OS Card UI component for NextBoot.
Displays a detected operating system with icon, status badges, details, and action buttons.
"""

import tkinter as tk
from core.os_detector import OSEntry
from ui.theme import Theme
from ui.icons import IconRenderer

class OSCard(tk.Frame):
    """An interactive card representing an installed OS."""

    def __init__(self, parent, entry: OSEntry, on_boot_clicked, on_default_clicked):
        super().__init__(
            parent,
            bg=Theme.BG_CARD,
            highlightthickness=1,
            highlightbackground=Theme.BORDER_ACTIVE if entry.is_next_boot else (Theme.BORDER_SUCCESS if entry.is_current else Theme.BORDER_DEFAULT),
            highlightcolor=Theme.BORDER_ACTIVE,
            padx=14,
            pady=12
        )
        self.entry = entry
        self.on_boot_clicked = on_boot_clicked
        self.on_default_clicked = on_default_clicked

        self._build_ui()
        self._bind_hover(self)

    def _build_ui(self):
        self.columnconfigure(1, weight=1)

        # 1. Left Icon (Canvas with procedural vector brand logo)
        icon_size = 46
        self.icon_canvas = tk.Canvas(
            self,
            width=icon_size,
            height=icon_size,
            bg=Theme.BG_CARD,
            bd=0,
            highlightthickness=0
        )
        self.icon_canvas.grid(row=0, column=0, rowspan=3, padx=(0, 14), sticky="n")
        IconRenderer.draw_os_icon(
            self.icon_canvas,
            cx=icon_size/2,
            cy=icon_size/2,
            size=icon_size,
            os_family=self.entry.os_family
        )

        # 2. Top Title and Badges row
        title_frame = tk.Frame(self, bg=Theme.BG_CARD)
        title_frame.grid(row=0, column=1, sticky="w", pady=(0, 2))

        name_lbl = tk.Label(
            title_frame,
            text=self.entry.name,
            font=Theme.FONT_CARD_TITLE,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD
        )
        name_lbl.pack(side="left", padx=(0, 8))

        # Status Badges
        if self.entry.is_current:
            b_curr = tk.Label(
                title_frame,
                text="● CURRENT RUNNING OS",
                font=Theme.FONT_BADGE,
                bg=Theme.BADGE_CURRENT_BG,
                fg=Theme.BADGE_CURRENT_FG,
                padx=6,
                pady=1
            )
            b_curr.pack(side="left", padx=(0, 5))

        if self.entry.is_next_boot:
            b_next = tk.Label(
                title_frame,
                text="⚡ SCHEDULED NEXT BOOT",
                font=Theme.FONT_BADGE,
                bg=Theme.BADGE_NEXT_BG,
                fg=Theme.BADGE_NEXT_FG,
                padx=6,
                pady=1
            )
            b_next.pack(side="left", padx=(0, 5))

        if self.entry.is_default:
            b_def = tk.Label(
                title_frame,
                text="★ DEFAULT BOOT",
                font=Theme.FONT_BADGE,
                bg=Theme.BADGE_DEFAULT_BG,
                fg=Theme.BADGE_DEFAULT_FG,
                padx=6,
                pady=1
            )
            b_def.pack(side="left", padx=(0, 5))

        # 3. Path / Device Details
        detail_text = self.entry.path or self.entry.device or "UEFI Boot Target"
        if len(detail_text) > 65:
            detail_text = "..." + detail_text[-62:]

        path_lbl = tk.Label(
            self,
            text=f"Path: {detail_text}",
            font=Theme.FONT_CARD_SUBTITLE,
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CARD
        )
        path_lbl.grid(row=1, column=1, sticky="w", pady=(1, 2))

        # 4. GUID / Type identifier
        type_str = "UEFI Firmware Entry" if self.entry.entry_type == "firmware_app" else (
            "Windows Boot Loader" if self.entry.entry_type == "osloader" else "Firmware Device"
        )
        guid_lbl = tk.Label(
            self,
            text=f"ID: {self.entry.identifier}  •  {type_str}",
            font=Theme.FONT_CARD_GUID,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CARD
        )
        guid_lbl.grid(row=2, column=1, sticky="w")

        # 5. Right Action Buttons
        actions_frame = tk.Frame(self, bg=Theme.BG_CARD)
        actions_frame.grid(row=0, column=2, rowspan=3, sticky="e", padx=(10, 0))

        if self.entry.is_current:
            # Active indicator
            curr_tag = tk.Label(
                actions_frame,
                text="Active System",
                font=Theme.FONT_BTN_SM,
                fg=Theme.TEXT_MUTED,
                bg=Theme.BG_CARD,
                padx=8,
                pady=4
            )
            curr_tag.pack(side="right")
        else:
            # Primary Boot Button
            btn_boot = tk.Button(
                actions_frame,
                text="🚀 Boot into this OS",
                font=Theme.FONT_BTN,
                bg=Theme.BTN_PRIMARY_BG,
                fg=Theme.BTN_PRIMARY_FG,
                activebackground=Theme.BTN_PRIMARY_HOVER,
                activeforeground=Theme.BTN_PRIMARY_FG,
                bd=0,
                padx=12,
                pady=6,
                cursor="hand2",
                command=lambda: self.on_boot_clicked(self.entry)
            )
            btn_boot.pack(side="right", padx=(6, 0))

            # Set Default Button
            if not self.entry.is_default and self.entry.os_family != "hardware":
                btn_def = tk.Button(
                    actions_frame,
                    text="Set Default",
                    font=Theme.FONT_BTN_SM,
                    bg=Theme.BTN_SECONDARY_BG,
                    fg=Theme.BTN_SECONDARY_FG,
                    activebackground=Theme.BTN_SECONDARY_HOVER,
                    activeforeground=Theme.BTN_SECONDARY_FG,
                    bd=0,
                    padx=9,
                    pady=6,
                    cursor="hand2",
                    command=lambda: self.on_default_clicked(self.entry)
                )
                btn_def.pack(side="right")

    def _bind_hover(self, widget):
        widget.bind("<Enter>", self._on_enter)
        widget.bind("<Leave>", self._on_leave)
        for child in widget.winfo_children():
            if not isinstance(child, tk.Button):
                self._bind_hover(child)

    def _on_enter(self, event):
        if not self.entry.is_next_boot and not self.entry.is_current:
            self.configure(highlightbackground=Theme.BORDER_HOVER, bg=Theme.BG_CARD_HOVER)
            self._set_bg(self, Theme.BG_CARD_HOVER)

    def _on_leave(self, event):
        if not self.entry.is_next_boot and not self.entry.is_current:
            self.configure(highlightbackground=Theme.BORDER_DEFAULT, bg=Theme.BG_CARD)
            self._set_bg(self, Theme.BG_CARD)

    def _set_bg(self, widget, color):
        if not isinstance(widget, tk.Button) and not isinstance(widget, tk.Canvas):
            try:
                widget.configure(bg=color)
            except Exception:
                pass
        for child in widget.winfo_children():
            self._set_bg(child, color)
