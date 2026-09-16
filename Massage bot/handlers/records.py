from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user, get_user_appointments, cancel_appointment
from aiogram.fsm.context import FSMContext
from .calendar import create_calendar_keyboard

router = Router()
@router.message(Command("my_records"))
async def my_records(message: Message):
    await show_records(message)

async def show_records(message: Message, user_id: int = None):
    if user_id is None:
        user_id = message.from_user.id
    user = await get_user(user_id)
    if user is None:
        await message.answer("❌ Сначала зарегистрируйтесь: /register")
        return
    appointments = await get_user_appointments(user[0])
    if not appointments:
        await message.answer("📭 У вас нет записей.")
        return
    text = "📋 Ваши записи:\n\n"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for app in appointments:
        app_id, date, time, status, service = app
        text += f"🔹 #{app_id} | {service or 'Массаж'} | {date} {time} | {status}\n"
        if status == "pending":
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text=f"❌ Отменить #{app_id}", callback_data=f"cancel_{app_id}")])
    await message.answer(text, reply_markup=keyboard)
    if status in ["pending", "confirmed"]:
            keyboard.inline_keyboard.append([
        InlineKeyboardButton(
            text=f"🔄 Перенести #{app_id}",
            callback_data=f"reschedule_{app_id}"
        )
    ])



@router.callback_query(F.data.startswith("cancel_"))
async def cancel_my_appointment(callback: CallbackQuery):
    appointment_id = int(callback.data.split("_")[1])
    await cancel_appointment(appointment_id)
    await callback.message.edit_text(f"✅ Запись #{appointment_id} отменена.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_records")]]))
    await callback.answer()

@router.callback_query(F.data == "refresh_records")
async def refresh_records(callback: CallbackQuery):
    await show_records(callback.message, callback.from_user.id)
    await callback.answer()

@router.callback_query(F.data.startswith("reschedule_"))
async def reschedule_appointment(callback: CallbackQuery, state: FSMContext):
    appointment_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    user = await get_user(user_id)
    if user is None:
        await callback.answer("Вы не зарегистрированы!", show_alert=True)
        return

    await state.update_data(old_appointment_id=appointment_id)
    await callback.message.answer("Выберите новую дату для записи:")
    keyboard = create_calendar_keyboard()
    await callback.message.answer(
        "Выберите новую дату:",
        reply_markup=keyboard
    )
    await callback.answer()