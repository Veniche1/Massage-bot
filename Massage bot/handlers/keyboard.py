from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


def get_main_reply_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Записаться")],
            [KeyboardButton(text="О массажисте")],
            [KeyboardButton(text="Помощь")]
        ],
        resize_keyboard=True
    )



def get_services_keyboard():
    """Клавиатура с выбором услуг"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Расслабляющий", callback_data="service_relax")],
        [InlineKeyboardButton(text="Лечебный (спина/шея)", callback_data="service_heal")],
        [InlineKeyboardButton(text="Антицеллюлитный", callback_data="service_cellulite")],
        [InlineKeyboardButton(text="Общий массаж", callback_data="service_general")]
    ])


def get_cancel_keyboard():

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="cancel")]
    ])