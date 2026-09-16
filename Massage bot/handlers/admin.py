from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from datetime import datetime, timedelta
import asyncio
from handlers.reviews import ask_review
import asyncio
from handlers.reviews import ask_review

from database import (
    get_all_appointments,
    update_appointment_status,
    get_appointment_by_id,
    get_user_by_db_id,
    get_user,
    block_date,
    unblock_date,
    get_blocked_dates
)

router = Router()
ADMIN_IDS = []

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Нет доступа")
        return
    pending = await get_all_appointments("pending")
    pending_count = len(pending)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📋 Новые заявки ({pending_count})", callback_data="admin_pending")],
        [InlineKeyboardButton(text="📅 Все записи", callback_data="admin_all")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🚫 Заблокировать дату", callback_data="admin_block")],
        [InlineKeyboardButton(text="🔓 Разблокировать дату", callback_data="admin_unblock")]
    ])
    await message.answer("🔐 **Админ-панель**", reply_markup=keyboard, parse_mode="Markdown")


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа")
        return
    pending = await get_all_appointments("pending")
    pending_count = len(pending)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📋 Новые заявки ({pending_count})", callback_data="admin_pending")],
        [InlineKeyboardButton(text="📅 Все записи", callback_data="admin_all")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🚫 Заблокировать дату", callback_data="admin_block")],
        [InlineKeyboardButton(text="🔓 Разблокировать дату", callback_data="admin_unblock")]
    ])
    await callback.message.edit_text("🔐 **Админ-панель**", reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "admin_pending")
async def show_pending(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа")
        return
    appointments = await get_all_appointments("pending")
    if not appointments:
        await callback.message.edit_text("📭 Новых заявок нет.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]]))
        await callback.answer()
        return
    text = "📋 **Новые заявки:**\n\n"
    for app in appointments[:5]:
        user = await get_user_by_db_id(app[1])
        if user:
            text += f"🔹 Заявка #{app[0]}\n   Клиент: {user[2]}\n   Дата: {app[2]} {app[3]}\n   Статус: ⏳ ожидает\n   ✅ /confirm_{app[0]} — подтвердить\n   ❌ /cancel_{app[0]} — отменить\n\n"
    if len(appointments) > 5:
        text += f"*Показано 5 из {len(appointments)}.*"
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]]))
    await callback.answer()


@router.message(Command("confirm"))
async def confirm_appointment(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Нет доступа")
        return
    parts = message.text.strip().split()
    if len(parts) < 2:
        await message.answer("❌ Используй: /confirm ID_ЗАПИСИ")
        return
    try:
        appointment_id = int(parts[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом!")
        return
    appointment = await get_appointment_by_id(appointment_id)
    if not appointment:
        await message.answer("❌ Запись не найдена")
        return
    if appointment[4] != "pending" and appointment[4] is not None:
        await message.answer(f"❌ Запись уже {appointment[4]}")
        return
    await update_appointment_status(appointment_id, "confirmed")
    user = await get_user_by_db_id(appointment[1])
    if user and user[1] is not None:
        await message.bot.send_message(
            user[1],
            f"✅ Ваша запись подтверждена!\n📅 {appointment[2]} {appointment[3]}"
        )
        asyncio.create_task(ask_review(message.bot, user[1], appointment_id))
        asyncio.create_task(ask_review(message.bot, user[1], appointment_id))
    else:
        await message.answer(f"⚠️ Клиент не найден, но запись #{appointment_id} подтверждена!")

@router.message(Command("cancel"))
async def cancel_appointment(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Нет доступа")
        return
    parts = message.text.strip().split()
    if len(parts) < 2:
        await message.answer("❌ Используй: /cancel ID_ЗАПИСИ [причина]")
        return
    try:
        appointment_id = int(parts[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом!")
        return
    reason = " ".join(parts[2:]) if len(parts) > 2 else "Не указана"
    appointment = await get_appointment_by_id(appointment_id)
    if not appointment:
        await message.answer("❌ Запись не найдена")
        return
    if appointment[4] != "pending" and appointment[4] is not None:
        await message.answer(f"❌ Запись уже {appointment[4]}")
        return
    await update_appointment_status(appointment_id, "canceled", reason)
    user = await get_user_by_db_id(appointment[1])
    if user and user[1] is not None:
        await message.bot.send_message(
            user[1],
            f"❌ Ваша запись отменена.\n📅 {appointment[2]} {appointment[3]}\nПричина: {reason}"
        )
    else:
        await message.answer(f"Клиент не найден, но запись #{appointment_id} отменена!")


@router.callback_query(F.data == "admin_all")
async def show_all_appointments(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа")
        return
    appointments = await get_all_appointments()
    if not appointments:
        await callback.message.edit_text("📭 Записей нет.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]]))
        await callback.answer()
        return
    text = "📅 **Все записи:**\n\n"
    for app in appointments[:10]:
        user = await get_user_by_db_id(app[1])
        if user:
            text += f"#{app[0]} | {user[2]} | {app[2]} {app[3]} | {app[4] or 'pending'}\n"
    if len(appointments) > 10:
        text += f"\n*Показано 10 из {len(appointments)}*"
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]]))
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def show_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа")
        return
    appointments = await get_all_appointments()
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    today_count = 0
    week_count = 0
    month_count = 0
    confirmed_count = 0
    for app in appointments:
        app_date = datetime.strptime(app[2], "%Y-%m-%d").date()
        if app_date == today:
            today_count += 1
        if app_date >= week_ago:
            week_count += 1
        if app_date >= month_ago:
            month_count += 1
        if app[4] == "confirmed":
            confirmed_count += 1
    text = "📊 **Статистика:**\n\n"
    text += f"📅 Сегодня: {today_count} записей\n"
    text += f"📅 За неделю: {week_count} записей\n"
    text += f"📅 За месяц: {month_count} записей\n"
    text += f"✅ Подтверждено: {confirmed_count} записей\n"
    text += f"⏳ Ожидают: {len([a for a in appointments if a[4] == 'pending'])} записей"
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]]))
    await callback.answer()


@router.callback_query(F.data == "admin_block")
async def block_date_start(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа")
        return
    await callback.message.edit_text("Введи дату для блокировки в формате **ГГГГ-ММ-ДД**", parse_mode="Markdown",
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                         [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]]))
    await callback.answer()


    @router.message(F.text)
    async def handle_block_date(message: Message):
        if not is_admin(message.from_user.id):
            return
        try:
            datetime.strptime(message.text.strip(), "%Y-%m-%d").date()
            date_str = message.text.strip()
        except ValueError:
            await message.answer("❌ Неверный формат. Используй ГГГГ-ММ-ДД")
            return
        await block_date(date_str)
        await message.answer(f"✅ Дата {date_str} заблокирована!")


@router.callback_query(F.data == "admin_unblock")
async def unblock_date_start(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа")
        return
    blocked = await get_blocked_dates()
    if not blocked:
        await callback.message.edit_text("📭 Нет заблокированных дат.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]]))
        await callback.answer()
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for date in blocked:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=f"🔓 {date[0]}", callback_data=f"unblock_{date[0]}")])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")])
    await callback.message.edit_text("Выбери дату для разблокировки:", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("unblock_"))
async def unblock_date_handler(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа")
        return
    date = callback.data.replace("unblock_", "")
    await unblock_date(date)
    await callback.message.edit_text(f"✅ Дата {date} разблокирована!")
    await callback.answer()

