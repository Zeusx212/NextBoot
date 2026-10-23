"""
Reboot Confirmation and Countdown Modal for NextBoot.
Allows user to trigger immediate restart, timed restart, or apply one-time boot for later.
"""

import tkinter as tk
from core.os_detector import OSEntry
from core.boot_manager import BootManager
from ui.theme import Theme
from ui.icons import IconRenderer

class RebootModal(tk.Toplevel):
    """Modern modal dialog confirming one-time boot sequence and restart mode."""

    def __init__(self, parent, entry: OSEntry, boot_manager: BootManager, on_success_callback=None):
        super().__init__(parent)
        self.entry = entry
        self.boot_manager = boot_manager
        self.on_success_callback = on_success_callback

        self.title("Confirm Boot Target - NextBoot")
        self.configure(bg=Theme.BG_MODAL)
        self.geometry("520x440")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Center on parent window
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        w = 520
        h = 440
        x = px + max(0, (pw - w) // 2)
        y = py + max(0, (ph - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.countdown_remaining = 0
        self.countdown_after_id = None

        self._build_ui()

    def _build_ui(self):
        # 1. Header Banner
        header = tk.Frame(self, bg=Theme.BG_HEADER, padx=20, pady=16)
        header.pack(fill="x")

        title_lbl = tk.Label(
            header,
            text=f"Boot into {self.entry.name}?",
            font=Theme.FONT_MODAL_TITLE,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_HEADER
        )
        title_lbl.pack(anchor="w")

        sub_lbl = tk.Label(
            header,
            text="One-Time UEFI / BCD Boot Sequence",
            font=Theme.FONT_SUBTITLE,
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_HEADER
        )
        sub_lbl.pack(anchor="w", pady=(2, 0))

        # 2. Body container
        body = tk.Frame(self, bg=Theme.BG_MODAL, padx=24, pady=16)
        body.pack(fill="both", expand=True)

        # Target OS Info Box
        info_box = tk.Frame(body, bg=Theme.BG_CARD, padx=14, pady=12, highlightthickness=1, highlightbackground=Theme.BORDER_DEFAULT)
        info_box.pack(fill="x", pady=(0, 14))

        canvas = tk.Canvas(info_box, width=36, height=36, bg=Theme.BG_CARD, bd=0, highlightthickness=0)
        canvas.pack(side="left", padx=(0, 12))
        IconRenderer.draw_os_icon(canvas, 18, 18, 36, self.entry.os_family)

        details_frame = tk.Frame(info_box, bg=Theme.BG_CARD)
        details_frame.pack(side="left", fill="x", expand=True)

        os_title = tk.Label(details_frame, text=self.entry.name, font=Theme.FONT_CARD_TITLE, fg=Theme.TEXT_PRIMARY, bg=Theme.BG_CARD)
        os_title.pack(anchor="w")

        path_text = self.entry.path or self.entry.device or "EFI Application"
        os_path = tk.Label(details_frame, text=f"Target: {path_text}", font=Theme.FONT_CARD_SUBTITLE, fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD)
        os_path.pack(anchor="w")

        # Safe Boot Explanation
        explain_frame = tk.Frame(body, bg=Theme.BG_MODAL)
        explain_frame.pack(fill="x", pady=(0, 16))

        explain_text = (
            "• NextBoot will configure your PC to jump directly into this OS on the next reboot.\n"
            "• This setting is temporary: your default boot order is preserved.\n"
            "• Subsequent restarts will return to your primary Windows environment."
        )
        lbl_explain = tk.Label(
            explain_frame,
            text=explain_text,
            font=Theme.FONT_CARD_SUBTITLE,
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_MODAL,
            justify="left"
        )
        lbl_explain.pack(anchor="w")

        # Countdown display (hidden initially)
        self.countdown_frame = tk.Frame(body, bg=Theme.BG_MODAL)
        self.lbl_countdown = tk.Label(
            self.countdown_frame,
            text="",
            font=Theme.FONT_COUNTDOWN,
            fg=Theme.BADGE_NEXT_FG,
            bg=Theme.BG_MODAL
        )
        self.lbl_countdown.pack(pady=4)

        self.lbl_countdown_msg = tk.Label(
            self.countdown_frame,
            text="System will restart automatically...",
            font=Theme.FONT_SUBTITLE,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_MODAL
        )
        self.lbl_countdown_msg.pack()

        # Status / Feedback label
        self.status_lbl = tk.Label(body, text="", font=Theme.FONT_SUBTITLE, fg=Theme.BADGE_CURRENT_FG, bg=Theme.BG_MODAL)
        self.status_lbl.pack(pady=(0, 6))

        # 3. Bottom Action Buttons
        self.buttons_frame = tk.Frame(self, bg=Theme.BG_HEADER, padx=20, pady=14)
        self.buttons_frame.pack(fill="x", side="bottom")

        self.btn_restart_now = tk.Button(
            self.buttons_frame,
            text="⚡ Restart Now",
            font=Theme.FONT_BTN,
            bg=Theme.BTN_PRIMARY_BG,
            fg=Theme.BTN_PRIMARY_FG,
            activebackground=Theme.BTN_PRIMARY_HOVER,
            activeforeground=Theme.BTN_PRIMARY_FG,
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=self._on_restart_now
        )
        self.btn_restart_now.pack(side="right", padx=(8, 0))

        self.btn_restart_10s = tk.Button(
            self.buttons_frame,
            text="⏱ Restart in 10s",
            font=Theme.FONT_BTN_SM,
            bg=Theme.BTN_SECONDARY_BG,
            fg=Theme.BTN_SECONDARY_FG,
            activebackground=Theme.BTN_SECONDARY_HOVER,
            activeforeground=Theme.BTN_SECONDARY_FG,
            bd=0,
            padx=10,
            pady=8,
            cursor="hand2",
            command=self._on_start_countdown
        )
        self.btn_restart_10s.pack(side="right", padx=(8, 0))

        self.btn_apply_later = tk.Button(
            self.buttons_frame,
            text="Apply (Restart Later)",
            font=Theme.FONT_BTN_SM,
            bg=Theme.BTN_SECONDARY_BG,
            fg=Theme.BTN_SECONDARY_FG,
            activebackground=Theme.BTN_SECONDARY_HOVER,
            activeforeground=Theme.BTN_SECONDARY_FG,
            bd=0,
            padx=10,
            pady=8,
            cursor="hand2",
            command=self._on_apply_later
        )
        self.btn_apply_later.pack(side="right", padx=(8, 0))

        self.btn_cancel = tk.Button(
            self.buttons_frame,
            text="Cancel",
            font=Theme.FONT_BTN_SM,
            bg=Theme.BG_HEADER,
            fg=Theme.TEXT_SECONDARY,
            bd=0,
            padx=10,
            pady=8,
            cursor="hand2",
            command=self.destroy
        )
        self.btn_cancel.pack(side="left")

    def _apply_boot_sequence(self) -> bool:
        success, msg = self.boot_manager.set_one_time_boot(self.entry)
        if not success:
            self.status_lbl.configure(text=f"Error: {msg}", fg=Theme.BTN_DANGER_BG)
            return False
        return True

    def _on_apply_later(self):
        if self._apply_boot_sequence():
            self.status_lbl.configure(
                text=f"✓ Next boot scheduled for {self.entry.name}!\nRestart your computer when ready.",
                fg=Theme.BADGE_CURRENT_FG
            )
            self.btn_restart_now.configure(state="disabled")
            self.btn_restart_10s.configure(state="disabled")
            self.btn_apply_later.configure(state="disabled")
            if self.on_success_callback:
                self.on_success_callback(self.entry)
            self.after(2000, self.destroy)

    def _on_restart_now(self):
        if self._apply_boot_sequence():
            self.status_lbl.configure(text="Restarting system...", fg=Theme.BADGE_CURRENT_FG)
            self.update()
            self.boot_manager.reboot(delay_seconds=0)

    def _on_start_countdown(self):
        if not self._apply_boot_sequence():
            return

        self.countdown_remaining = 10
        self.countdown_frame.pack(fill="x", pady=(0, 10))

        # Hide options and show Abort button
        self.btn_restart_now.pack_forget()
        self.btn_restart_10s.pack_forget()
        self.btn_apply_later.pack_forget()
        self.btn_cancel.pack_forget()

        self.btn_abort = tk.Button(
            self.buttons_frame,
            text="🛑 ABORT RESTART",
            font=Theme.FONT_BTN,
            bg=Theme.BTN_DANGER_BG,
            fg=Theme.BTN_DANGER_FG,
            activebackground=Theme.BTN_DANGER_HOVER,
            activeforeground=Theme.BTN_DANGER_FG,
            bd=0,
            padx=16,
            pady=8,
            cursor="hand2",
            command=self._abort_countdown
        )
        self.btn_abort.pack(fill="x")

        self._tick_countdown()

    def _tick_countdown(self):
        if self.countdown_remaining > 0:
            self.lbl_countdown.configure(text=str(self.countdown_remaining))
            self.countdown_remaining -= 1
            self.countdown_after_id = self.after(1000, self._tick_countdown)
        else:
            self.lbl_countdown.configure(text="0")
            self.lbl_countdown_msg.configure(text="Rebooting now...")
            self.update()
            self.boot_manager.reboot(delay_seconds=0)

    def _abort_countdown(self):
        if self.countdown_after_id:
            self.after_cancel(self.countdown_after_id)
            self.countdown_after_id = None
        self.boot_manager.abort_reboot()
        self.boot_manager.clear_one_time_boot()
        self.destroy()
