import os
from flask import Flask, request

from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# -----------------------------------------
# Fest kodierte Tokens
# -----------------------------------------
TOKEN = "7743077318:AAEZw-EUa0A4kL65wjkjbnI-37nA6UsH8k0"
CHAT_ID = "7743077318"

print(f"DEBUG: Verwende Bot-Token: {TOKEN[:5]}...")
print(f"DEBUG: Verwende Chat-ID: {CHAT_ID}")

# Telegram Application bauen (Webhook statt Polling)
application = Application.builder().token(TOKEN).build()

# Zustände für ConversationHandler
WAITING_FOR_CATEGORY, WAITING_FOR_TASK, WAITING_FOR_DELETE_TASK = range(3)

# /start-Befehl
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hallo! Ich bin dein Telegram-Bot 🚀\n"
        "Verfügbare Befehle:\n"
        "/start - Bot starten\n"
        "/help - Hilfe anzeigen\n"
        "/addtask - Aufgabe hinzufügen\n"
        "/showtasks - Aufgaben anzeigen\n"
        "/deletetask - Aufgabe löschen"
    )

# /help-Befehl
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Du kannst folgende Befehle verwenden:\n"
        "/start - Bot starten\n"
        "/help - Hilfe anzeigen\n"
        "/addtask - Aufgabe hinzufügen\n"
        "/showtasks - Aufgaben anzeigen\n"
        "/deletetask - Aufgabe löschen"
    )

# /addtask - Kategorie abfragen
async def addtask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Daily Goals", "Weekly Goals", "Langfristige Goals"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Wohin möchtest du die Aufgabe hinzufügen?", reply_markup=reply_markup)
    return WAITING_FOR_CATEGORY

# /addtask - Aufgabe speichern
async def save_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = update.message.text
    context.user_data['category'] = category
    await update.message.reply_text(f"Was möchtest du zu den {category} hinzufügen?", reply_markup=ReplyKeyboardRemove())
    return WAITING_FOR_TASK

# /addtask - Aufgabe bestätigen
async def confirm_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task = update.message.text
    category = context.user_data['category']
    file_name = f"{category.lower().replace(' ', '_')}.txt"
    with open(file_name, "a") as file:
        file.write(task + "\n")
    await update.message.reply_text(f"Aufgabe hinzugefügt: {task} in {category}!")
    return ConversationHandler.END

# /showtasks - Kategorie abfragen
async def showtasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Daily Goals", "Weekly Goals", "Langfristige Goals"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Welche Aufgaben möchtest du sehen?", reply_markup=reply_markup)
    return WAITING_FOR_CATEGORY

# /showtasks - Aufgaben anzeigen
async def display_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = update.message.text
    file_name = f"{category.lower().replace(' ', '_')}.txt"
    try:
        with open(file_name, "r") as file:
            tasks = file.readlines()
        if tasks:
            await update.message.reply_text(f"{category}:\n" + ''.join(tasks))
        else:
            await update.message.reply_text(f"Keine Aufgaben in {category} gefunden.")
    except FileNotFoundError:
        await update.message.reply_text(f"Es gibt noch keine Aufgaben in {category}.")
    return ConversationHandler.END

# /deletetask - Kategorie abfragen
async def deletetask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Daily Goals", "Weekly Goals", "Langfristige Goals"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Aus welcher Kategorie möchtest du eine Aufgabe löschen?", reply_markup=reply_markup)
    return WAITING_FOR_CATEGORY

# /deletetask - Aufgabe löschen
async def select_task_to_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = update.message.text
    context.user_data['category'] = category
    file_name = f"{category.lower().replace(' ', '_')}.txt"
    try:
        with open(file_name, "r") as file:
            tasks = file.readlines()
        if tasks:
            keyboard = [[task.strip()] for task in tasks]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text("Welche Aufgabe möchtest du löschen?", reply_markup=reply_markup)
            return WAITING_FOR_DELETE_TASK
        else:
            await update.message.reply_text(f"Keine Aufgaben in {category} gefunden.", reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END
    except FileNotFoundError:
        await update.message.reply_text(f"Keine Aufgaben in {category} gefunden.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

# /deletetask - Aufgabe bestätigen
async def confirm_delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task_to_delete = update.message.text
    category = context.user_data['category']
    file_name = f"{category.lower().replace(' ', '_')}.txt"
    try:
        with open(file_name, "r") as file:
            tasks = file.readlines()
        tasks = [task for task in tasks if task.strip() != task_to_delete]
        with open(file_name, "w") as file:
            file.writelines(tasks)
        await update.message.reply_text(f"Aufgabe gelöscht: {task_to_delete}")
    except FileNotFoundError:
        await update.message.reply_text("Fehler beim Löschen der Aufgabe.")
    return ConversationHandler.END

# Automatische Nachricht um 6:00 Uhr
async def send_daily_tasks(context: ContextTypes.DEFAULT_TYPE):
    file_name = "daily_goals.txt"
    try:
        with open(file_name, "r") as file:
            tasks = file.readlines()
        if tasks:
            await context.bot.send_message(chat_id=CHAT_ID, text="Heutige Aufgaben:\n" + ''.join(tasks))
        else:
            await context.bot.send_message(chat_id=CHAT_ID, text="Keine täglichen Aufgaben für heute.")
    except FileNotFoundError:
        await context.bot.send_message(chat_id=CHAT_ID, text="Keine täglichen Aufgaben für heute.")

# -----------------------------------------
# Flask-App für Webhook
# -----------------------------------------
app = Flask(__name__)

@app.route("/")
def index():
    return "Hallo, dein Telegram-Web-Bot läuft (Flask 2.0.3 / Werkzeug 2.0.3)."

@app.route(f"/webhook/{TOKEN}", methods=["POST"])
async def receive_update():
    json_data = request.get_json(force=True)
    update = Update.de_json(json_data, application.bot)
    await application.update_queue.put(update)
    return "OK", 200

# -----------------------------------------
# Setup-Scheduler & Webhook vor erster Anfrage
# -----------------------------------------
@app.before_first_request
async def configure_bot():
    print("DEBUG: Bot-Konfiguration startet...")
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_daily_tasks, "cron", hour=6, minute=0, args=[application.bot])
    scheduler.start()
    print("DEBUG: Scheduler läuft...")

    # Conversation Handler definieren
    conv_handler_add = ConversationHandler(
        entry_points=[CommandHandler("addtask", addtask)],
        states={
            WAITING_FOR_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_task)],
            WAITING_FOR_TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_task)],
        },
        fallbacks=[CommandHandler("cancel", start)],
    )
    conv_handler_show = ConversationHandler(
        entry_points=[CommandHandler("showtasks", showtasks)],
        states={
            WAITING_FOR_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, display_tasks)],
        },
        fallbacks=[CommandHandler("cancel", start)],
    )
    conv_handler_delete = ConversationHandler(
        entry_points=[CommandHandler("deletetask", deletetask)],
        states={
            WAITING_FOR_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_task_to_delete)],
            WAITING_FOR_DELETE_TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_delete_task)],
        },
        fallbacks=[CommandHandler("cancel", start)],
    )

    # Handler zur App hinzufügen
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(conv_handler_add)
    application.add_handler(conv_handler_show)
    application.add_handler(conv_handler_delete)

    # Webhook setzen (Render-URL anpassen!)
    render_url = os.getenv("RENDER_EXTERNAL_URL", "https://DEINERENDERURL.onrender.com")
    webhook_url = f"{render_url}/webhook/{TOKEN}"
    await application.bot.set_webhook(url=webhook_url)
    print(f"DEBUG: Webhook gesetzt auf: {webhook_url}")

# Lokaler Start
if __name__ == "__bot__":
    app.run(debug=True, port=5000)
