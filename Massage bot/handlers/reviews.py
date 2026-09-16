from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import get_user, get_appointment_by_id, save_review, get_reviews
import asyncio

router = Router()

class ReviewStates(StatesGroup):
    waiting_comment = State()

async def ask_review(bot, user_id: int, appointment_id: int):
    await asyncio.sleep(3600)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐️ 1", callback_data=f"rate_{appointment_id}_1")],
        [InlineKeyboardButton(text="⭐️⭐️ 2", callback_data=f"rate_{appointment_id}_2")],
        [InlineKeyboardButton(text="⭐️⭐️⭐️ 3", callback_data=f"rate_{appointment_id}_3")],
        [InlineKeyboardButton(text="⭐️⭐️⭐️⭐️ 4", callback_data=f"rate_{appointment_id}_4")],
        [InlineKeyboardButton(text="⭐️⭐️⭐️⭐️⭐️ 5", callback_data=f"rate_{appointment_id}_5")]
    ])
    
    await bot.send_message(
        user_id,
        "🗣 Как прошёл массаж?\nОцените от 1 до 5:",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("rate_"))
async def handle_rate(callback: CallbackQuery, state: FSMContext):
    _, appointment_id, rating = callback.data.split("_")
    appointment_id = int(appointment_id)
    rating = int(rating)
    user_id = callback.from_user.id

    user = await get_user(user_id)
    if user is None:
        await callback.answer("Вы не зарегистрированы!", show_alert=True)
        return
    await state.update_data(appointment_id=appointment_id, rating=rating)
    await state.set_state(ReviewStates.waiting_comment)

    await callback.message.edit_text(f"⭐️ Спасибо за оценку {rating}!")
    await callback.answer()

    await callback.message.answer("Напишите ваш отзыв (или отправьте '-' чтобы пропустить):")
@router.message(ReviewStates.waiting_comment, F.text)
async def save_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    rating = data.get("rating")
    appointment_id = data.get("appointment_id")
    comment = message.text.strip()

    user = await get_user(user_id)
    if user is None:
        await message.answer("Вы не зарегистрированы!")
        await state.clear()
        return

    if comment == "-":
        comment = "Без комментария"

    await save_review(user[0], appointment_id, rating, comment)
    await message.answer("Спасибо! Ваш отзыв сохранён.")
    await state.clear()

@router.message(Command("reviews"))
async def show_reviews(message: Message):
    reviews = await get_reviews(5)
    if not reviews:
        await message.answer("Пока нет отзывов.")
        return
    text = "Отзывы наших клиентов:\n\n"
    for name, rating, comment in reviews:
        stars = "⭐" * rating
        text += f"{stars} {name}\n"
        if comment and comment != "Без комментария":
            text += f"💬 {comment}\n"
        text += "\n"
    await message.answer(text, parse_mode="Markdown")
    