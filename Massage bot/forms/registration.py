from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from handlers.keyboard import get_main_reply_keyboard
from database import add_user, get_user
import re

router = Router()

class Form(StatesGroup):
    name = State()
    age = State()

def is_russian_name(name):
    return re.match(r'^[А-Яа-яЁё\s]+$', name) is not None

@router.message(Command("register"))
async def cmd_register(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if await get_user(user_id):
        await message.answer("Вы уже зарегистрированы")
        return

    await state.set_state(Form.name)
    await message.answer(
        "Давайте запишемся на массаж!\nВведите ваше имя:",
        reply_markup=get_main_reply_keyboard()
    )

@router.message(Form.name, F.text)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()

    if not is_russian_name(name):
        await message.answer("Имя должно быть на русском, без цифр и символов!")
        return

    if len(name) < 2:
        await message.answer("Слишком короткое имя!")
        return

    await state.update_data(name=name)
    await message.answer("Отлично!\nА теперь введите свой возраст:")
    await state.set_state(Form.age)

@router.message(Form.age, F.text)
async def process_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Возраст укажите числом!")
        return

    age = int(message.text)
    if age < 16 or age > 75:
        await message.answer("Возраст должен быть от 16 до 75 лет!")
        return

    data = await state.get_data()
    name = data["name"]

    await add_user(message.from_user.id, name, age)
    await message.answer(f" Вы зарегистрированы!\nИмя: {name}\nВозраст: {age}\nТеперь напишите команду /help для продолжения записи")
    await state.clear()