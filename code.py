import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from aiogram.types import CallbackQuery

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Ошибка: Токен бота не найден! Проверь .env файл.")

logging.basicConfig(level=logging.INFO)

current_pairings = {}
users = {}

SUBJECT_CHAT_LINKS = {
    "Высшая математика": "https://t.me/+GrZtERbAswBiZjgy",
    "Программирование": "https://t.me/+OJEqXi2DFIxmODEy",
    "Русский язык": "https://t.me/+t8rAcHOvPRw3M2Fi",
    "Иностранные языки": "https://t.me/+sFYMivtyiiw1MGUy",
    "История": "https://t.me/+N57kMOevoWE1NGUy",
    "Научная деятельность": "https://t.me/+9Iu0mYOnqtwyNDYy",
    "Философия": "https://t.me/+HbqVLZ8x5gI4OTky"
}

session = AiohttpSession()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML), session=session)
dp = Dispatcher()


SUBJECTS = [
    "Высшая математика", "Программирование", "Русский язык",
    "Иностранные языки", "История", "Научная деятельность", "Философия"
]

DIRECTION = [
    "ИВТ", "ПМИ", "ИБАС",
    "ИМФ", "ФИИТ", "11 направление", "12 направление"
]

COURSE = [
    "1", "2", "3",
    "4", "5"
]

def get_like_response_keyboard(liker_id: int):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="✉ Ответить", callback_data=f"reply_{liker_id}")
    keyboard.button(text="🚫 Игнорировать", callback_data="ignore")
    return keyboard.as_markup()

menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Найти напарника")],
        [KeyboardButton(text="🏠 Зайти в отдельную группу")],
        [KeyboardButton(text="✏️ Заполнить анкету заново")],
        [KeyboardButton(text="❌ Отключить анкету")]
    ],
    resize_keyboard=True
)

profile_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="👍 Лайк", callback_data="like")],
    [InlineKeyboardButton(text="👎 Дизлайк", callback_data="dislike")],
    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
])

class Registration(StatesGroup):
    waiting_for_hobby = State()
    waiting_for_name = State()
    waiting_for_direction = State()
    waiting_for_course = State()
    waiting_for_photo = State()
    waiting_for_subjects = State()
    waiting_for_help_subject = State()
    waiting_for_comment = State()



@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in users:
        await message.answer("Ты уже зарегистрирован! Используй меню.", reply_markup=menu_keyboard)
    else:
        await message.answer("Привет! Как тебя зовут?")
        await state.set_state(Registration.waiting_for_name)

@dp.message(Registration.waiting_for_name, F.text)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=direction)] for direction in DIRECTION],
        resize_keyboard=True
    )

    await message.answer("Отлично! Выбери своё направление обучения:", reply_markup=keyboard)
    await state.set_state(Registration.waiting_for_direction)

@dp.message(Registration.waiting_for_direction, F.text)
async def process_direction(message: types.Message, state: FSMContext):
    if message.text not in DIRECTION:
        await message.answer("Пожалуйста, выбери направление из предложенных вариантов!")
        return

    await state.update_data(direction=message.text)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=course)] for course in COURSE],
        resize_keyboard=True
    )
    await message.answer("Хорошо! Выбери свой курс:", reply_markup=keyboard)
    await state.set_state(Registration.waiting_for_course)

@dp.message(Registration.waiting_for_course, F.text)
async def process_course(message: types.Message, state: FSMContext):
    if message.text not in COURSE:
        await message.answer("Пожалуйста, выбери курс из предложенных вариантов!")
        return

    await state.update_data(course=message.text)
    data = await state.get_data()
    await message.answer(
        f"Отлично! Ты выбрал направление: {data['direction']}, курс: {data['course']}.",
        reply_markup=ReplyKeyboardRemove()
    )

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Пропустить")]],
        resize_keyboard=True
    )
    await message.answer("Расскажи немного о себе.", reply_markup=keyboard)
    await state.set_state(Registration.waiting_for_hobby)

@dp.message(Registration.waiting_for_hobby, F.text)
async def process_hobby(message: types.Message, state: FSMContext):
    if message.text == "Пропустить":
        await state.update_data(hobby=" ")
    else:
        await state.update_data(hobby=message.text)

    await message.answer("Теперь отправь своё фото.", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Registration.waiting_for_photo)

@dp.message(Registration.waiting_for_photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo=photo_id)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=subj)] for subj in SUBJECTS] + [[KeyboardButton(text="✅ Завершить выбор")]],
        resize_keyboard=True
    )

    await message.answer("Теперь выбери предметы, в которых ты разбираешься:", reply_markup=keyboard)
    await state.update_data(subjects=[], available_subjects=SUBJECTS.copy())
    await state.set_state(Registration.waiting_for_subjects)

@dp.message(Registration.waiting_for_subjects, F.text)
async def process_subject_selection(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    available_subjects = user_data["available_subjects"]

    if message.text == "✅ Завершить выбор":
        if not user_data["subjects"]:
            await message.answer("Ты не выбрал ни одного предмета! Выбери хотя бы один.")
            return

        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=subj)] for subj in SUBJECTS],
            resize_keyboard=True
        )

        await message.answer("Теперь выбери предмет, с которым тебе нужна помощь:", reply_markup=keyboard)
        await state.set_state(Registration.waiting_for_help_subject)
        return

    if message.text in available_subjects:
        available_subjects.remove(message.text)
        user_data["subjects"].append(message.text)

        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=subj)] for subj in available_subjects] + [[KeyboardButton(text="✅ Завершить выбор")]],
            resize_keyboard=True
        )

        await state.update_data(subjects=user_data["subjects"], available_subjects=available_subjects)
        await message.answer(f"Добавлено: {message.text}. Можешь выбрать ещё или нажать   '✅ Завершить выбор'.", reply_markup=keyboard)
    else:
        await message.answer("Выбери предмет из списка!")

@dp.message(Registration.waiting_for_help_subject, F.text)
async def process_help_subject(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    available_help_subjects = [subj for subj in SUBJECTS if subj not in user_data.get("subjects", [])]
    if message.text not in available_help_subjects:
        await message.answer("Этот предмет ты и так знаешь. Пожалуйста, выбери другой.")
        return

    await state.update_data(help_subject=message.text)
    users[message.from_user.id] = await state.get_data()

    await message.answer(
        "✅ Регистрация завершена! Теперь ты можешь искать напарников, заходить в группы или изменить анкету.",
        reply_markup=menu_keyboard
    )

    user_data = users[message.from_user.id]
    text = (
        f"📜 <b>Анкета пользователя</b>\n\n"
        f"👤 <b>Имя:</b> {user_data['name']}\n"
        f"📚 <b>Направление:</b> {user_data['direction']}\n"
        f"🎓 <b>Курс:</b> {user_data['course']}\n"
        f"🎨 <b>О себе:</b> {user_data['hobby']}\n"
        f"📖 <b>Разбирается в:</b> {', '.join(user_data['subjects'])}\n"
        f"❗ <b>Нужна помощь в:</b> {user_data['help_subject']}"
    )

    await bot.send_photo(
        chat_id=message.from_user.id,
        photo=user_data["photo"],
        caption=text,
        reply_markup=menu_keyboard
    )

    await state.clear()



def find_matching_users(user_id):
    if user_id not in users:
        return []

    my_help_subject = users[user_id]["help_subject"]

    matching_users = [
        uid for uid, data in users.items()
        if uid != user_id and my_help_subject in data["subjects"]
    ]

    return matching_users



@dp.message(F.text == "🔍 Найти напарника")
async def find_partner(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    matching_users = find_matching_users(user_id)

    if not matching_users:
        await message.answer("😔 Подходящих напарников пока нет. Попробуй позже!", reply_markup=menu_keyboard)
        return

    await state.update_data(matching_users=matching_users, current_index=0)

    await message.answer("🔍 Ищу напарника...", reply_markup=ReplyKeyboardRemove())

    await send_next_profile(message, state)

async def send_next_profile(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    matching_users = user_data.get("matching_users", [])
    current_index = user_data.get("current_index", 0)

    if current_index >= len(matching_users):
        await message.answer("📌 Анкеты закончились! Попробуй позже.", reply_markup=menu_keyboard)
        await state.clear()
        return

    target_user_id = matching_users[current_index]
    target_user = users[target_user_id]

    profile_text = (
        f"📜 <b>Анкета напарника</b>\n\n"
        f"👤 <b>Имя:</b> {target_user['name']}\n"
        f"📚 <b>Направление:</b> {target_user['direction']}\n"
        f"🎓 <b>Курс:</b> {target_user['course']}\n"
        f"🎨 <b>О себе:</b> {target_user['hobby']}\n"
        f"📖 <b>Разбирается в:</b> {', '.join(target_user['subjects'])}\n"
        f"❗ <b>Не разбирается в:</b> {users[message.from_user.id]['help_subject']}"
    )

    await bot.send_photo(
        chat_id=message.from_user.id,
        photo=target_user["photo"],
        caption=profile_text,
        reply_markup=profile_keyboard
    )

    await state.update_data(current_index=current_index + 1)

@dp.callback_query(F.data == "like")
async def like_user(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    matching_users = user_data.get("matching_users", [])
    current_index = user_data.get("current_index", 0) - 1

    if current_index < 0 or current_index >= len(matching_users):
        await callback.answer("Ошибка: не найден пользователь для лайка.")
        return

    liked_user_id = matching_users[current_index]

    await state.update_data(liked_user=liked_user_id)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Пропустить")]],
        resize_keyboard=True
    )
    await callback.message.answer("Напиши комментарий:", reply_markup=keyboard)
    await state.set_state(Registration.waiting_for_comment)

@dp.message(Registration.waiting_for_comment, F.text)
async def process_comment(message: types.Message, state: FSMContext):

    user_data = await state.get_data()
    liked_user_id = user_data.get("liked_user")

    if not liked_user_id:
        await message.answer("Ошибка: не найден лайкнутый пользователь.")
        return

    comment = message.text if message.text != "Пропустить" else "Без комментариев"
    liker_data = users.get(message.from_user.id)

    if not liker_data:
        await message.answer("Ошибка: твоя анкета не найдена.")
        return

    profile_text = (
        f"📜 <b>Анкета лайкнувшего тебя пользователя</b>\n\n"
        f"👤 <b>Имя:</b> {liker_data['name']}\n"
        f"📚 <b>Направление:</b> {liker_data['direction']}\n"
        f"🎓 <b>Курс:</b> {liker_data['course']}\n"
        f"🎨 <b>О себе:</b> {liker_data['hobby']}\n"
        f"📖 <b>Разбирается в:</b> {', '.join(liker_data['subjects'])}\n"
        f"❗ <b>Нужна помощь в:</b> {liker_data['help_subject']}\n\n"
        f"💬 <b>Комментарий:</b> {comment}"
    )

    try:
        await bot.send_photo(
            chat_id=liked_user_id,
            photo=liker_data["photo"],
            caption=profile_text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_like_response_keyboard(message.from_user.id)
        )
    except Exception as e:
        logging.error(f"Ошибка при отправке лайка: {e}")

    await message.answer("Лайк отправлен! Показываю следующую анкету...", reply_markup=ReplyKeyboardRemove())
    await send_next_profile(message, state)

@dp.callback_query(F.data.startswith("reply_"))
async def process_reply(callback: types.CallbackQuery):
    liker_id = int(callback.data.split("_")[1])

    liker = await bot.get_chat(liker_id)
    responder = await bot.get_chat(callback.from_user.id)

    async def handle_callback(callback, liker, responder, keyboard, liker_id):
        # ... other code ...

        if not liker.username or not responder.username:
            retry_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data=f"retry_link_{liker_id}")]
            ])

            await callback.message.answer(
                "❌ Один из пользователей скрыл свой аккаунт.\n"
                "📝 Убедитесь, что ваш профиль открыт в настройках Telegram и нажмите 'Попробовать снова'.",
                reply_markup=retry_keyboard
            )
            await callback.answer()
            return

    liker_link = f"https://t.me/{liker.username}"
    responder_link = f"https://t.me/{responder.username}"

    await bot.send_message(
        chat_id=liker_id,
        text=f"💌 <b>Отлично! Пользователь принял твой лайк!</b>\n\n"
             f"👉 Теперь ты можешь начать общение с <a href='{responder_link}'>напарником</a>",
        parse_mode=ParseMode.HTML,
        reply_markup = menu_keyboard
    )

    await callback.message.answer(
        f"💌 <b>Ты принял(а) лайк!</b>\n\n"
        f"👉 Теперь ты можешь начать общение с <a href='{liker_link}'>напарником</a>",
        parse_mode=ParseMode.HTML,
        reply_markup=menu_keyboard
    )

    await callback.answer("Ссылки на Telegram отправлены обоим пользователям!")


@dp.callback_query(F.data == "ignore")
async def process_ignore(callback: types.CallbackQuery):
    await callback.message.answer("❌ Ты проигнорировал лайк.")
    await callback.answer()

@dp.callback_query(F.data == "dislike")
async def dislike_user(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("👎 Ты поставил дизлайк.")

    user_data = await state.get_data()
    current_index = user_data.get("current_index", 0)
    matching_users = user_data.get("matching_users", [])

    current_index += 1
    await state.update_data(current_index=current_index)

    if current_index < len(matching_users):
        await send_next_profile(callback.message, state)
    else:
        await callback.message.answer("📌 Анкеты закончились! Попробуй позже.", reply_markup=menu_keyboard)
        await state.clear()

@dp.callback_query(F.data == "main_menu")
async def process_main_menu(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🏠 Возвращаемся в главное меню.", reply_markup=menu_keyboard)
    await state.clear()
    await callback.answer()



@dp.message(F.text == "🏠 Зайти в отдельную группу")
async def choose_group(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if user_id not in users:
        await message.answer("📚 Выбираем предмет...", reply_markup=ReplyKeyboardRemove())
        await message.answer("Сначала заполни анкету! Напиши /start, чтобы начать.")
        return

    user_data = users[user_id]
    user_subjects = user_data["subjects"]
    help_subject = user_data["help_subject"]

    if not user_subjects:
        await message.answer("Ты не выбрал ни одного предмета при регистрации. Заполни анкету заново через /start.")
        return

    keyboard = ReplyKeyboardBuilder()

    for subject in user_subjects:
        keyboard.button(text=subject)

    if help_subject and help_subject not in user_subjects:
        keyboard.button(text=help_subject)

    keyboard.button(text="🏠 Главное меню")

    keyboard.adjust(2)

    await message.answer("Выбери предмет, чтобы получить ссылку на соответствующий чат:",
                         reply_markup=keyboard.as_markup(resize_keyboard=True))

@dp.message(lambda message: message.text in SUBJECT_CHAT_LINKS)
async def send_chat_link(message: types.Message):
    user_id = message.from_user.id
    user_data = users.get(user_id)

    if not user_data:
        await message.answer("Твоя анкета не найдена. Напиши /start, чтобы зарегистрироваться.")
        return

    chosen_subject = message.text

    links = []

    if chosen_subject in SUBJECT_CHAT_LINKS:
        links.append(f"Вот ссылка на чат по предмету <b>{chosen_subject}</b>:\n{SUBJECT_CHAT_LINKS[chosen_subject]}")

    await message.answer("\n\n".join(links), parse_mode=ParseMode.HTML)

@dp.message(F.text == "🏠 Главное меню")
async def back_to_main_menu(message: types.Message):
    await message.answer("🔙 Ты вернулся в главное меню.", reply_markup=menu_keyboard)



@dp.message(F.text == "✏️ Заполнить анкету заново")
async def reset_form(message: types.Message, state: FSMContext):
    users.pop(message.from_user.id, None)
    await state.clear()
    await message.answer("Анкета сброшена. Давай начнём заново! Как тебя зовут?")
    await state.set_state(Registration.waiting_for_name)



@dp.message(F.text == "❌ Отключить анкету")
async def disable_profile(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in users:
        users.pop(user_id)
        await state.clear()
        await message.answer("Твоя анкета отключена. Если захочешь вернуться — напиши /start.", reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer("Твоя анкета и так отключена.", reply_markup=ReplyKeyboardRemove())



async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
