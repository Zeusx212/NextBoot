"""
Theme and styling definitions for NextBoot.
Provides modern Windows 11 Fluent Dark / Light theme palettes.
"""

class Theme:
    # Modern Fluent Dark Palette
    BG_ROOT = "#121316"          # Deep rich window background
    BG_CARD = "#1c1e22"          # Surface for OS cards
    BG_CARD_HOVER = "#25282e"    # Card hover state
    BG_CARD_ACTIVE = "#1e293b"   # Highlighted / active border
    BG_HEADER = "#181a1d"        # Top title & status header
    BG_MODAL = "#181a1d"         # Dialog background
    BG_INPUT = "#22252a"         # Input / text field

    BORDER_DEFAULT = "#2a2d34"   # Card subtle stroke
    BORDER_HOVER = "#3f444e"
    BORDER_ACTIVE = "#38bdf8"    # Active focus blue
    BORDER_SUCCESS = "#10b981"

    TEXT_PRIMARY = "#f8fafc"     # High-contrast title & body
    TEXT_SECONDARY = "#94a3b8"   # Path & details
    TEXT_MUTED = "#64748b"       # Identifier GUIDs
    TEXT_ON_ACCENT = "#ffffff"

    # Status Badges
    BADGE_CURRENT_BG = "#064e3b"
    BADGE_CURRENT_FG = "#34d399"
    BADGE_DEFAULT_BG = "#1e3a8a"
    BADGE_DEFAULT_FG = "#60a5fa"
    BADGE_NEXT_BG = "#78350f"
    BADGE_NEXT_FG = "#fbbf24"
    BADGE_HW_BG = "#4c1d95"
    BADGE_HW_FG = "#c084fc"

    # Primary Action Buttons
    BTN_PRIMARY_BG = "#2563eb"       # Vibrant Windows Blue
    BTN_PRIMARY_HOVER = "#1d4ed8"
    BTN_PRIMARY_FG = "#ffffff"

    BTN_SECONDARY_BG = "#2a2d34"
    BTN_SECONDARY_HOVER = "#373b44"
    BTN_SECONDARY_FG = "#e2e8f0"

    BTN_DANGER_BG = "#dc2626"
    BTN_DANGER_HOVER = "#b91c1c"
    BTN_DANGER_FG = "#ffffff"

    BTN_SUCCESS_BG = "#16a34a"
    BTN_SUCCESS_HOVER = "#15803d"
    BTN_SUCCESS_FG = "#ffffff"

    # Font definitions
    FONT_FAMILY = "Segoe UI"
    FONT_TITLE = (FONT_FAMILY, 15, "bold")
    FONT_SUBTITLE = (FONT_FAMILY, 10)
    FONT_CARD_TITLE = (FONT_FAMILY, 12, "bold")
    FONT_CARD_SUBTITLE = (FONT_FAMILY, 9)
    FONT_CARD_GUID = ("Consolas", 8)
    FONT_BADGE = (FONT_FAMILY, 8, "bold")
    FONT_BTN = (FONT_FAMILY, 9, "bold")
    FONT_BTN_SM = (FONT_FAMILY, 8, "bold")
    FONT_MODAL_TITLE = (FONT_FAMILY, 14, "bold")
    FONT_COUNTDOWN = (FONT_FAMILY, 32, "bold")
