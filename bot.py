import telebot
import requests
import json
import os
from datetime import datetime, timedelta

# Bot token and admin ID
BOT_TOKEN = ""
ADMIN_ID = 
CHANNELS = ["@MrGhostXFF", "@GrayCipherBD"]

bot = telebot.TeleBot(BOT_TOKEN)

# Paths for JSON files
USER_DB = "users.json"
REDEEM_DB = "redeem.json"

# Initialize JSON databases
def load_or_create_json(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        else:
            with open(file_path, "w") as f:
                json.dump({}, f)
            return {}
    except json.JSONDecodeError:
        print(f"Error: {file_path} contains invalid JSON. Resetting the file.")
        with open(file_path, "w") as f:
            json.dump({}, f)
        return {}

users = load_or_create_json(USER_DB)
redeem_data = load_or_create_json(REDEEM_DB)

# Save JSON data
def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

# Check user subscription
def check_subscription(user_id):
    for channel in CHANNELS:
        status = bot.get_chat_member(channel, user_id).status
        if status not in ["member", "administrator", "creator"]:
            return False
    return True

# Ensure user exists in database
def ensure_user(user_id, name):
    if str(user_id) not in users:
        users[str(user_id)] = {
            "name": name,
            "points": 0,
            "last_bonus": None,
            "redeemed_codes": []
        }
        save_json(USER_DB, users)

# Add or deduct points
def add_points(user_id, points):
    users[str(user_id)]["points"] += points
    save_json(USER_DB, users)

def deduct_points(user_id, points):
    users[str(user_id)]["points"] -= points
    save_json(USER_DB, users)

# Command: /start
@bot.message_handler(commands=["start"])
def welcome_user(message):
    ensure_user(message.from_user.id, message.from_user.first_name)
    if check_subscription(message.from_user.id):
        send_main_menu(message.chat.id)
    else:
        markup = telebot.types.InlineKeyboardMarkup()
        for channel in CHANNELS:
            markup.add(telebot.types.InlineKeyboardButton("✨ Join Channel ✨", url=f"https://t.me/{channel[1:]}"))
        bot.send_message(
            message.chat.id,
            "🔥 **Welcome to the bot!**\n\nPlease join our channels to unlock the features. 😊",
            parse_mode="Markdown",
            reply_markup=markup
        )

# Show main menu
def send_main_menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = ["👤 My Account", "🎁 Bonus", "💥 Spam", "📩 Contact", "🔑 Redeem Code"]
    markup.add(*buttons)
    bot.send_message(chat_id, "**🤯 Thann Kachh, Booyah! 💀**", parse_mode="Markdown", reply_markup=markup)

# My Account Button
@bot.message_handler(func=lambda msg: msg.text == "👤 My Account")
def my_account(message):
    user_data = users.get(str(message.from_user.id), {})
    if user_data:
        bot.reply_to(
            message,
            f"👤 **Name:** {user_data['name']}\n🔑 **User ID:** {message.from_user.id}\n💰 **Points:** {user_data['points']}",
            parse_mode="Markdown"
        )

# Bonus Button
@bot.message_handler(func=lambda msg: msg.text == "🎁 Bonus")
def bonus_points(message):
    user = users.get(str(message.from_user.id))
    if not user:
        return
    last_bonus = user.get("last_bonus")
    now = datetime.now()
    if last_bonus and datetime.strptime(last_bonus, "%Y-%m-%d %H:%M:%S") + timedelta(hours=24) > now:
        bot.reply_to(message, "⚠️ You can only claim your bonus every 24 hours.")
    else:
        add_points(message.from_user.id, 50)
        users[str(message.from_user.id)]["last_bonus"] = now.strftime("%Y-%m-%d %H:%M:%S")
        save_json(USER_DB, users)
        bot.reply_to(message, "🎉 **50 bonus points added to your account!**", parse_mode="Markdown")

# Contact Button
@bot.message_handler(func=lambda msg: msg.text == "📩 Contact")
def contact(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("📨 Contact Us", url="https://t.me/MrGhostXBOT"))
    bot.send_message(message.chat.id, "💬 **Need help? Contact us below:**", parse_mode="Markdown", reply_markup=markup)

# Spam Button
@bot.message_handler(func=lambda msg: msg.text == "💥 Spam")
def spam_action(message):
    user = users.get(str(message.from_user.id))
    if user and user["points"] >= 100:
        msg = bot.reply_to(message, "🔢 **Enter Target Free Fire UID:**", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_spam, message.from_user.id)
    else:
        bot.reply_to(message, "⚠️ **You need at least 100 points to use this feature.**", parse_mode="Markdown")

def process_spam(msg, user_id):
    target_uid = msg.text.strip()
    api_url = f"https://graycipherbd.serv00.net/FF/spam.php?uid={target_uid}"
    
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            deduct_points(user_id, 100)
            bot.reply_to(msg, f"✅ **Spam request successful!**\n\n💬 **API Response:** `{response.text}`", parse_mode="Markdown")
        else:
            bot.reply_to(msg, f"❌ **Failed to process request.**\n\n⚠️ **API Status Code:** {response.status_code}", parse_mode="Markdown")
    except requests.exceptions.RequestException as e:
        bot.reply_to(msg, f"❌ **Error:** Could not reach API.\n\n⚠️ **Details:** {e}", parse_mode="Markdown")

# Redeem Code Button
@bot.message_handler(func=lambda msg: msg.text == "🔑 Redeem Code")
def redeem_code_handler(message):
    msg = bot.reply_to(message, "🔑 **Enter your redeem code:**", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_redeem)

def process_redeem(msg):
    user_id = str(msg.from_user.id)
    code = msg.text.strip()

    if user_id not in users:
        bot.reply_to(msg, "❌ **User data not found. Please try again.**", parse_mode="Markdown")
        return

    if "redeemed_codes" not in users[user_id]:
        users[user_id]["redeemed_codes"] = []
        save_json(USER_DB, users)

    if code in redeem_data and redeem_data[code]["uses"] > 0:
        if code in users[user_id]["redeemed_codes"]:
            bot.reply_to(msg, "❌ **You have already used this redeem code.**", parse_mode="Markdown")
        else:
            add_points(msg.from_user.id, redeem_data[code]["points"])
            redeem_data[code]["uses"] -= 1
            users[user_id]["redeemed_codes"].append(code)
            save_json(REDEEM_DB, redeem_data)
            save_json(USER_DB, users)
            bot.reply_to(msg, "🎉 **Redeem successful! Points added to your account.**", parse_mode="Markdown")
    else:
        bot.reply_to(msg, "❌ **Invalid or expired redeem code.**", parse_mode="Markdown")

# Admin Commands
@bot.message_handler(commands=["createcode"])
def create_code(message):
    if message.from_user.id == ADMIN_ID:
        try:
            _, code, points, uses = message.text.split()
            points, uses = int(points), int(uses)
            redeem_data[code] = {"points": points, "uses": uses}
            save_json(REDEEM_DB, redeem_data)
            bot.reply_to(message, f"✅ **Redeem code '{code}' created!**", parse_mode="Markdown")
        except ValueError:
            bot.reply_to(message, "⚠️ **Usage:** /createcode <code> <points> <uses>", parse_mode="Markdown")

print("✨ Bot is online!")
try:
    bot.polling(non_stop=True)
except Exception as e:
    print(f"❌ Bot stopped due to an error: {e}")
