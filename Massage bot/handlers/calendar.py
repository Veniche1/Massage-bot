from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from datetime import datetime, timedelta
import calendar
from database import get_user, get_user_appointment_on_date, is_time_taken, get_booked_dates, get_all_appointments, add_appointment, cancel_appointment
from .keyboard import get_main_reply_keyboard, get_services_keyboard
from .commands import check_registration
from aiogram.fsm.context import FSMContext


router = Router()



def get_month_days(year: int, month: int):
    first_day = datetime(year, month, 1)
    start_weekday = first_day.weekday()
    _, days_in_month = calendar.monthrange(year, month)

    days_grid = []
    week = []

    for _ in range(start_weekday):
        week.append(None)

    for day in range(1, days_in_month + 1):
        week.append(day)
        if len(week) == 7:
            days_grid.append(week)
            week = []

    while len(week) < 7:
        week.append(None)
    if week:
        days_grid.append(week)

    return days_grid


def can_select_date(date_str: str) -> bool:
    today = datetime.now()
    select = datetime.strptime(date_str, "%Y-%m-%d").date()
    if select < today:
        return False
    max_date = today + timedelta(days=60)
    if select > max_date:
        return False
    return True


def create_calendar_keyboard(year: int = None, month: int = None):
    if year is None or month is None:
        now = datetime.now()
        year = now.year
        month = now.month

    months_ru = [
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]
    weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    month_year_text = f"{months_ru[month-1]} {year}"

    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="◀️", callback_data=f"cal_prev_{year}_{month}"),
        InlineKeyboardButton(text=month_year_text, callback_data="cal_ignore"),
        InlineKeyboardButton(text="▶️", callback_data=f"cal_next_{year}_{month}")
    ])

    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text=day, callback_data="cal_ignore") for day in weekdays
    ])

    days_grid = get_month_days(year, month)
    today = datetime.now().date()
    max_date = today + timedelta(days=60)

    for week in days_grid:
        row = []
        for day in week:
            if day is None:
                row.append(InlineKeyboardButton(text=" ", callback_data="cal_ignore"))
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                selected = datetime.strptime(date_str, "%Y-%m-%d").date()
                if selected < today or selected > max_date:
                    row.append(InlineKeyboardButton(text="❌", callback_data="cal_ignore"))
                else:
                    row.append(InlineKeyboardButton(
                        text=str(day),
                        callback_data=f"cal_day_{date_str}"
                    ))
        keyboard.inline_keyboard.append(row)

    return keyboard


@router.message(Command("calendar"))
@router.message(F.text == "Записаться")
async def cmd_calendar(message: Message):
    if not await check_registration(message):
        return

    keyboard = get_services_keyboard()
    await message.answer(
        "🧘 **Выберите услугу:**",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("service_"))
async def service_selected(callback: CallbackQuery):
    service_map = {
        "service_relax": "Расслабляющий",
        "service_heal": "Лечебный (спина/шея)",
        "service_cellulite": "Антицеллюлитный",
        "service_general": "Общий массаж"
    }

    service_name = service_map.get(callback.data, "Массаж")
    keyboard = create_calendar_keyboard()
    await callback.message.edit_text(
        f"✅ Вы выбрали: **{service_name}**\n\n📅 Теперь выберите дату:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("cal_"))
async def handle_calendar(callback: CallbackQuery,  state: FSMContext):
    data = callback.data.split("_")
    action = data[1]

    if action == "ignore":
        await callback.answer()
        return

    if action in ["prev", "next"]:
        year = int(data[2])
        month = int(data[3])

        if action == "prev":
            month -= 1
            if month < 1:
                month = 12
                year -= 1
        else:
            month += 1
            if month > 12:
                month = 1
                year += 1

        today = datetime.now()
        current_month = today.month
        current_year = today.year

        if year < current_year or (year == current_year and month < current_month):
            await callback.message.answer("Нельзя вернуться в прошлое")
            return

        max_month = current_month + 1
        max_year = current_year
        if max_month > 12:
            max_month -= 12
            max_year += 1

        if year > max_year or (year == max_year and month > max_month):
            await callback.message.answer("Нельзя выбрать дальше 1 месяца")
            return

        keyboard = create_calendar_keyboard(year, month)
        await callback.message.edit_text(
            "Выберите дату:",
            reply_markup=keyboard
        )
        await callback.answer()

    elif action == "day":
        date_str = data[2]
        time_keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        time_slots = ["10:00", "11:00", "12:00", "13:00", "14:00",
                      "15:00", "16:00", "17:00", "18:00", "19:00", "20:00"]
        row = []
        for time in time_slots:
            row.append(InlineKeyboardButton(
                text=time,
                callback_data=f"cal_time_{date_str}_{time}"
            ))
            if len(row) == 2:
                time_keyboard.inline_keyboard.append(row)
                row = []
        if row:
            time_keyboard.inline_keyboard.append(row)

        time_keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="🔙 Назад", callback_data="cal_back")
        ])
        await callback.message.edit_text(
            f"Вы выбрали: {date_str}\n\nТеперь выберите время:",
            reply_markup=time_keyboard
        )
        await callback.answer()

    elif action == "time":
        date_str = data[2]
        time_str = data[3]
        user_id = callback.from_user.id

        user = await get_user(user_id)
        if user is None:
            await callback.message.edit_text("Вы не зарегистрированы! /register")
            await callback.answer()
            return

       
        state_data = await state.get_data()
        old_appointment_id = state_data.get("old_appointment_id")

        if old_appointment_id:
            await cancel_appointment(old_appointment_id)
            await add_appointment(user[0], date_str, time_str)
            await callback.message.edit_text(
                f"✅ Запись перенесена на {date_str} {time_str}!\n"
                f"Старая запись отменена."
            )
            await state.clear()
        else:
            # Обычная запись
            existing = await get_user_appointment_on_date(user[0], date_str)
            if existing:
                await callback.message.edit_text(
                    f"❌ Вы уже записаны на {date_str}!\nВы не можете записаться дважды."
                )
                await callback.answer()
                return

            if await is_time_taken(date_str, time_str):
                await callback.message.edit_text(
                    f"❌ Время {time_str} уже занято.\nВыберите другое."
                )
                await callback.answer()
                return

            await add_appointment(user[0], date_str, time_str)
            await callback.message.edit_text(
                f"✅ Вы записаны на массаж!\n\n"
                f"Дата: {date_str}\n"
                f"Время: {time_str}\n\n"
                f"Ждите подтверждения."
            )
            await callback.answer()

    elif action == "back":
        keyboard = create_calendar_keyboard()
        await callback.message.edit_text(
            "📅 Выберите дату для записи:",
            reply_markup=keyboard
        )
        await callback.answer()


@router.callback_query(F.data == "open_calendar")
async def open_calendar(callback: CallbackQuery):
    await callback.message.answer("📅 Используй команду /calendar")
    await callback.answer()