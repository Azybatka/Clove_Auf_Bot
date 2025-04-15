import json
import random
import os
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
import wikipedia
from datetime import datetime
from telegram.ext import MessageHandler
from telegram.ext import filters




FORUM_LINK = "https://t.me/+N0qpf7Tf9WNkNDMy"


BAD_WORDS = {"дурак", "идиот", "тупой", "сука", "fuck", "shit"}  # можно расширить

async def auto_moderate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    text = message.text.lower()
    if any(bad_word in text for bad_word in BAD_WORDS):
        try:
            await message.delete()
            await context.bot.send_message(
                chat_id=message.chat_id,
                text=f"⚠️ Сообщение от @{message.from_user.username or message.from_user.first_name} удалено из-за нарушений правил."
            )
        except Exception as e:
            print("Ошибка при удалении сообщения:", e)



wikipedia.set_lang("ru")

DATA_FILE = "users.json"
PROGRESS_FILE = "progress.json"

def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_users(users):
    with open(DATA_FILE, "w") as f:
        json.dump(users, f, indent=2)

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_progress(data):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f, indent=2)

        
# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚀 Рост", callback_data="open_growth")],
        [InlineKeyboardButton("💬 Открытый чат/форум", url=FORUM_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Выбирай действие:", reply_markup=reply_markup)


# /luck
async def luck(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or f"user{user_id}"
    users = load_users()

    if not any(u['id'] == user_id for u in users):
        users.append({"id": user_id, "username": username})
        save_users(users)
        await update.message.reply_text(f"🌱 Привет, @{username}! Ты добавлен в базу. Попробуй снова команду /luck.")
        return

    others = [u for u in users if u['id'] != user_id]
    if not others:
        await update.message.reply_text("😕 Пока что ты один в системе. Позови друзей или попробуй позже!")
        return

    match = random.choice(others)
    await update.message.reply_text(f"🎉 Ты нашёл удачу! Познакомься с: @{match['username']}")

# /knowledge
async def knowledge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❓ Чтобы воспользоваться базой знаний, напиши:\n/knowledge [твой вопрос]")
        return

    query = " ".join(context.args)
    try:
        summary = wikipedia.summary(query, sentences=3)
        page = wikipedia.page(query)
        url = page.url

        response = f"📚 *Ответ из Википедии:*\n\n*{query}*\n\n{summary}\n\n🔗 [Читать подробнее]({url})"
        await update.message.reply_markdown(response)

    except wikipedia.exceptions.DisambiguationError as e:
        await update.message.reply_text(f"🔍 Уточни вопрос. Возможные варианты:\n{', '.join(e.options[:5])}...")
    except wikipedia.exceptions.PageError:
        await update.message.reply_text("❌ Ничего не найдено. Попробуй переформулировать вопрос.")
    except Exception as e:
        await update.message.reply_text("⚠️ Произошла ошибка при поиске.")
        print(e)

# /news
async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌍 Научные открытия", callback_data='topic_science')],
        [InlineKeyboardButton("🧠 Психология и саморазвитие", callback_data='topic_mind')],
        [InlineKeyboardButton("🍏 Здоровье и питание", callback_data='topic_health')],
        [InlineKeyboardButton("📱 Технологии и лайфхаки", callback_data='topic_tech')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🗞 Выбери тему для вдохновляющих новостей:", reply_markup=reply_markup)

def get_news_by_query(query="технологии"):
    url = f"https://news.google.com/rss/search?q={query}&hl=ru&gl=RU&ceid=RU:ru"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'xml')
    items = soup.find_all('item')[:3]

    if not items:
        return "😕 Не удалось получить новости."

    result = f"🗞 *Новости по теме: {query.capitalize()}*\n"
    for i, item in enumerate(items, 1):
        title = item.title.text
        link = item.link.text
        pubDate = item.pubDate.text[:16]
        result += f"\n*{i}. {title}*\n🗓 {pubDate} | [Читать]({link})\n"
    return result

async def handle_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'topic_tech':
        news_text = get_news_by_query("технологии")
    elif query.data == 'topic_science':
        news_text = get_news_by_query("наука")
    elif query.data == 'topic_mind':
        news_text = get_news_by_query("психология")
    elif query.data == 'topic_health':
        news_text = get_news_by_query("здоровье")
    else:
        news_text = "🤔 Неизвестная тема."

    await query.edit_message_text(text=news_text, parse_mode="Markdown", disable_web_page_preview=False)

# /growth и /grow
async def growth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await grow(update, context)

async def grow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎯 Фокус", callback_data="growth_focus")],
        [InlineKeyboardButton("🧘 Расслабление", callback_data="growth_relax")],
        [InlineKeyboardButton("🧠 Память", callback_data="growth_memory")],
        [InlineKeyboardButton("💼 Продуктивность", callback_data="growth_productivity")],
        [InlineKeyboardButton("💪 Самодисциплина", callback_data="growth_discipline")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🚀 Выбери направление личного роста:", reply_markup=reply_markup)

async def handle_growth_direction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    direction = query.data.replace("growth_", "")
    today = datetime.now().strftime("%Y-%m-%d")

    progress = load_progress()
    user_data = progress.get(user_id, {})


    # Если новое направление или новая дата — обновим прогресс
    if user_data.get("direction") != direction or user_data.get("date") != today:
        streak = user_data.get("streak", 0)
        if user_data.get("date") != today:
            streak += 1

        user_data = {
            "direction": direction,
            "date": today,
            "done": False,
            "streak": streak
        }
        progress[user_id] = user_data
        save_progress(progress)

    tasks = {
        "focus": "📌 Задание: 5 минут полной концентрации без телефона.",
        "relax": "📌 Задание: 4 медленных глубоких вдоха.",
        "memory": "📌 Задание: Запомни и повтори 5 новых слов.",
        "productivity": "📌 Задание: Запиши 3 дела и выполни одно.",
        "discipline": "📌 Задание: Сделай что-то полезное, что откладывал."
    }

    task = tasks.get(direction, "❔ Нет задания.")
    done = user_data.get("done", False)
    streak = user_data.get("streak", 0)

    keyboard = []
    if not done:
        keyboard = [[InlineKeyboardButton("✅ Выполнено", callback_data=f"done_{direction}")]]
    else:
        task = "🎉 Задание уже выполнено на сегодня. Отличная работа!"

    text = f"🌱 Направление: *{direction.capitalize()}*\n📅 Дата: {today}\n🔥 Серия дней: {streak}\n\n{task}"
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    

async def mark_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    direction = query.data.replace("done_", "")
    today = datetime.now().strftime("%Y-%m-%d")

    progress = load_progress()
    user_data = progress.get(user_id, {
        "direction": direction,
        "date": today,
        "done": False,
        "streak": 1
    })

    user_data["done"] = True
    user_data["date"] = today
    user_data["direction"] = direction
    progress[user_id] = user_data
    save_progress(progress)

    await query.edit_message_text(text="✅ Задание выполнено! Возвращайся завтра 💚")

# Main
if __name__ == '__main__':
    import asyncio
    from telegram.ext import Application

    TOKEN = "7922994694:AAHqLf8exzAAuaVmUjrp62ujJgFvOqOCZRw"

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("luck", luck))
    app.add_handler(CommandHandler("knowledge", knowledge))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("growth", growth))
    app.add_handler(CommandHandler("grow", grow))
    app.add_handler(CallbackQueryHandler(handle_topic, pattern="^topic_"))
    app.add_handler(CallbackQueryHandler(handle_growth_direction, pattern="^growth_"))
    app.add_handler(CallbackQueryHandler(mark_done, pattern="^done_"))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, auto_moderate))



    print("🤖 Бот запущен...")
    app.run_polling()
