from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from .keyboard import get_main_reply_keyboard, get_services_keyboard
from database import get_user

router = Router()


async def check_registration(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)

    if user is None:
        await message.answer(
            "Сначала зарегистрируйтесь\n"
            "Используйте команду /register"
        )
        return False
    return True


@router.message(Command("start"))
@router.message(F.text.lower() == "старт")
async def cmd_start(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)

    if user:
        await message.answer(
            "✅ **Вы уже зарегистрированы!**\n\n"
            "📅 Чтобы записаться на массаж, нажмите кнопку ниже или введите /calendar\n"
            "ℹ️ Подробнее обо мне: /info\n"
            "❓ Помощь: /help",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="📅 Записаться", callback_data="open_calendar")]
                ]
            ),
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "👋 **Привет!**\n\n"
            "Это бот для записи на массаж.\n"
            "Меня зовут Лариса, я профессиональный массажист.\n\n"
            "📝 Для начала зарегистрируйтесь: /register\n"
            "ℹ️ Подробнее обо мне: /info",
            reply_markup=get_main_reply_keyboard(),
            parse_mode="Markdown"
        )


@router.message(Command("help"))
@router.message(F.text.lower() == "помощь")
async def cmd_help(message: Message):
    if not await check_registration(message):
        return

    await message.answer(
        "Доступные команды:\n\n"
        "/start — Главное меню\n"
        "/register — Регистрация\n"
        "/calendar — Запись на массаж\n"
        "/my_records — Мои записи\n"
        "/info — О массажисте\n"
        "/help — Помощь\n"
        "/reviews — отзывы от других клиентов\n\n"
        "📅 Как записаться?\n"
        "1️⃣ Зарегистрируйтесь через /register\n"
        "2️⃣ Выберите дату и время через /calendar\n"
        "3️⃣ Дождитесь подтверждения от мастера\n\n"
        "Остались вопросы?  Напишите мне в личные сообщения: @username\n"
        "Нашли ошибку или хотите сказать что можно до работать напишите техподдержке: ",
        reply_markup=get_main_reply_keyboard()
    )


@router.message(Command("info"))
@router.message(F.text.lower() == "о массажисте")
async def cmd_about(message: Message):
    if not await check_registration(message):
        return

    await message.answer(
        "**Массажист Лариса**\n\n"
        "Твои руки запомнят это прикосновение.\n\n"
        "Представь: ты заходишь в уютный кабинет с мягким светом, пахнет маслом лаванды. "
        "Лариса встречает тебя с улыбкой — и ты понимаешь: здесь тебя не будут ломать и терпеть боль.\n\n"
        "Она работает 3 года. И не просто «делает массаж» — она чувствует твое тело, как будто читает его.\n\n"
        "✨ **Что она умеет:**\n"
        "✅ Снимать головную боль и убирать тяжесть в плечах\n"
        "✅ Убирать отёки и возвращать лимфоток\n"
        "✅ Разбудить мышцы и убрать зажимы\n"
        "✅ Полное расслабление без боли\n\n"
        "**Почему к ней идут и возвращаются:**\n"
        "Лариса не работает «по шаблону». Она подстраивается под тебя.\n\n"
        "**Что говорят те, кто уже был:**\n"
        "«Лариса, я до тебя думала, что массаж — это больно. А ты делаешь так, что я засыпаю на столе». "
        "«3 сеанса — и я перестала пить обезболивающие». \n\n"
        "**Как попасть:**\n"
        "Запишись сейчас — она не берёт больше 5 человек в день, потому что каждому отдаёт всю свою энергию.\n\n"
        "Запись: /calendar",
        reply_markup=get_main_reply_keyboard(),
        parse_mode="Markdown"
    )
