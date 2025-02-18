from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import requests

BOT_TOKEN = '8059718400:AAFIwtQXkQXg9hzS14hM3I2ZebGf_QjM2iQ'
ADMIN_ID = 7969253195

# Data storage
user_data = {}
redeem_codes = {}
live_member_count = 0


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global live_member_count
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name
    args = context.args

    # Handle invite system
    referrer_id = args[0].replace("Bot", "") if args else None
    if referrer_id and int(referrer_id) != user_id:
        if user_id not in user_data:
            user_data[user_id] = {'credits': 3, 'referrer': int(referrer_id)}
            user_data[int(referrer_id)]['credits'] += 1
            await context.bot.send_message(
                int(referrer_id),
                "🎉 Someone joined using your invite! You earned +1 credit. 💰"
            )

    if user_id not in user_data:
        user_data[user_id] = {'credits': 3, 'referrer': None}
        live_member_count += 1

    invite_link = f"https://t.me/{context.bot.username}?start=Bot{user_id}"
    welcome_msg = f"👋 Welcome, {user_name} 🎉\n\n💡 Explore the bot options below.\n__________________________"

    keyboard = [
        [InlineKeyboardButton("🐍 WORM GPT 🐍", callback_data="worm_gpt"),
         InlineKeyboardButton("💰 CREDIT 💰", callback_data="credit")],
        [InlineKeyboardButton("🔥 DEV 🔥", url="https://t.me/CSFTEAM3")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_msg, reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "worm_gpt":
        keyboard = [[InlineKeyboardButton("BACK", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("💬 Ask your query below:", reply_markup=reply_markup)

    elif query.data == "credit":
        credits = user_data.get(user_id, {}).get("credits", 0)
        invite_link = f"https://t.me/{context.bot.username}?start=Bot{user_id}"
        message = f"💰 Your Credits: {credits}\n\n📊 Total Members: {live_member_count}\n\n" \
                  f"Invite friends to earn more credits! 🎉\n\n" \
                  f"Your invite link: [Click Here]({invite_link})"
        keyboard = [[InlineKeyboardButton("BACK", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")

    elif query.data == "main_menu":
        keyboard = [
            [InlineKeyboardButton("🐍 WORM GPT 🐍", callback_data="worm_gpt"),
             InlineKeyboardButton("💰 CREDIT 💰", callback_data="credit")],
            [InlineKeyboardButton("🔥 DEV 🔥", url="https://t.me/CSFTEAM3")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("💡 Back to the main menu. Choose an option below.", reply_markup=reply_markup)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if user_data.get(user_id, {}).get("credits", 0) > 0:
        api_url = f"https://ngyt777gworm.tiiny.io/?question={text}"
        response = requests.get(api_url)
        
        # UTF-8 decode and split response if multiple parameters exist
        try:
            answer = response.content.decode("utf-8").strip()
            if "\n" in answer:
                answer = answer.split("\n")[0]  # Take the first meaningful response
        except:
            answer = "Error decoding response."

        if "```" not in answer and any(tag in answer.lower() for tag in ["<html>", "<code>", "<script>", "function", "class"]):
            answer = f"```\n{answer}\n```"

        user_data[user_id]['credits'] -= 1
        new_credits = user_data[user_id]['credits']
        await update.message.reply_text(f"💡 Answer 💡 \n\n{answer}", parse_mode="Markdown")

        keyboard = [[InlineKeyboardButton("BACK", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if new_credits > 0:
            await update.message.reply_text(f"Your remaining credits: {new_credits} 💰", reply_markup=reply_markup)
        else:
            invite_link = f"https://t.me/{context.bot.username}?start=Bot{user_id}"
            await update.message.reply_text(f"⚠️ Your credits are over.\n\n"
                                            f"Invite friends to earn more! 🎉\n\n"
                                            f"Your invite link: [Click Here]({invite_link})",
                                            parse_mode="Markdown", reply_markup=reply_markup)
    else:
        invite_link = f"https://t.me/{context.bot.username}?start=Bot{user_id}"
        await update.message.reply_text(f"⚠️ You have no credits left.\n\n"
                                        f"Invite friends to earn more! 🚀\n\n"
                                        f"Your invite link: [Click Here]({invite_link})",
                                        parse_mode="Markdown")


async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    try:
        args = context.args
        code = args[0]
        value = int(args[1].strip("()"))

        redeem_codes[code] = value
        await update.message.reply_text(f"✅ Redeem code `{code}` generated for {value} credits!", parse_mode="Markdown")

    except (IndexError, ValueError):
        await update.message.reply_text("❌ Invalid format. Use: /redeem <code> (<value>)")


async def handle_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        code = context.args[0]

        if code in redeem_codes:
            value = redeem_codes.pop(code)
            user_data[user_id]['credits'] += value
            await update.message.reply_text(f"✅ Redeem successful! Your credits: {user_data[user_id]['credits']} 💰")
        else:
            await update.message.reply_text("❌ Invalid or expired redeem code.")
    except IndexError:
        await update.message.reply_text("❌ Please provide a redeem code.")


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("redeem", redeem))
    application.add_handler(CommandHandler("use_redeem", handle_redeem))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))

    application.run_polling()


if __name__ == "__main__":
    main()
        
