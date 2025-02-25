from typing import Optional, List
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup
)


@staticmethod
def button_builder(text: str, callback_data: str, type: Optional[str] = None) -> InlineKeyboardButton:
    """Build an inline keyboard button."""
    if type == "switch_inline_query_current_chat":
        return InlineKeyboardButton(text=text, switch_inline_query_current_chat=callback_data)
    return InlineKeyboardButton(text=text, callback_data=callback_data)

@staticmethod
def build_keyboard(buttons: List[InlineKeyboardButton], row_width: int = 1) -> InlineKeyboardMarkup:
    """Build an inline keyboard from a list of buttons."""
    keyboard = []
    row = []
    for button in buttons:
        if len(row) == row_width:
            keyboard.append(row)
            row = []
        row.append(button)
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
