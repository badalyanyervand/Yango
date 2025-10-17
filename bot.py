# -*- coding: utf-8 -*-
import asyncio
import nest_asyncio
import telegram
import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ======== CONFIG ========
BOT_TOKEN = "ԱՅՍՏԵՂ_ԴԻՐ_ՔՈ_TOKENԸ"
TELEGRAM_USERNAME = "yandexgopartner"
PHONE = "+37477554677"
FORM_URL = "https://forms.gle/tKVJgHu1KCNZhCvRA"
ADMIN_ID = 123456789  # ⚠️ Դիր քո Telegram ID-ն այստեղ (գտնելու համար գրիր բոտին /myid)

# HTTP ֆիքս
telegram.request._baserequest._DEFAULT_HTTP_IMPL = "httpx"
nest_asyncio.apply()

# Օգտատերերի տվյալները պահելու ֆայլ
USERS_FILE = "users.json"
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

# ======== ԿՈՃԱԿՆԵՐ ========
def kb_back_and_call(back_data: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Գրիր Telegram-ում", url=f"https://t.me/{TELEGRAM_USERNAME}")],
        [InlineKeyboardButton("📞 WhatsApp", url=f"https://wa.me/{PHONE.replace('+','')}")],
        [InlineKeyboardButton("⬅️ Հետ գնալ", callback_data=back_data)]
    ])

def kb_main():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤝 Ցանկանում եմ համագործակցել", callback_data="partner")],
        [InlineKeyboardButton("🚖 Արդեն համագործակցում եմ Ձեզ հետ", callback_data="existing")]
    ])

def kb_partner_areas():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚖 Տաքսի", callback_data="taxi")],
        [InlineKeyboardButton("📦 Առաքում", callback_data="delivery")],
        [InlineKeyboardButton("⬅️ Հետ գնալ", callback_data="main")]
    ])

def kb_taxi_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💛 Մեր մասին", callback_data="taxi_about")],
        [InlineKeyboardButton("📄 Տաքսոպարկի պայմանները", callback_data="taxi_terms")],
        [InlineKeyboardButton("🎁 Բոնուսային համակարգ", callback_data="taxi_bonus")],
        [InlineKeyboardButton("🤝 Դառնալ գործընկեր", callback_data="taxi_partner")],
        [InlineKeyboardButton("⬅️ Հետ գնալ", callback_data="partner")]
    ])

def kb_delivery_menu_root():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚗 Մեքենայով առաքումներ", callback_data="delivery_car")],
        [InlineKeyboardButton("🛵 Մոպեդով առաքումներ", callback_data="delivery_moped")],
        [InlineKeyboardButton("🚶‍♂️ Ոտքով առաքումներ", callback_data="delivery_foot")],
        [InlineKeyboardButton("🚛 Բեռնատարով առաքումներ", callback_data="delivery_truck")],
        [InlineKeyboardButton("⬅️ Հետ գնալ", callback_data="partner")]
    ])

def kb_delivery_section(prefix: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💛 Մեր մասին", callback_data=f"{prefix}_about")],
        [InlineKeyboardButton("📄 Պայմաններ", callback_data=f"{prefix}_terms")],
        [InlineKeyboardButton("🎁 Բոնուսային համակարգ", callback_data=f"{prefix}_bonus")],
        [InlineKeyboardButton("🤝 Դառնալ գործընկեր", callback_data=f"{prefix}_partner")],
        [InlineKeyboardButton("⬅️ Հետ գնալ", callback_data="delivery")]
    ])

# ======== ՏԵՔՍՏԵՐ ========
TAXI_ABOUT = (
    "💛 *Մեր մասին — Y TAXI*\n\n"
    "Մենք հանդիսանում ենք *Յանդեքս Գո* ծառայության գործընկերը Հայաստանում 2017թ-ից։\n"
    "Մեզ հետ համագործակցում են ավելի քան *10,000 վարորդներ*։\n\n"
    "📍 Հասցե — ք. Երևան, Տիգրան Մեծ 55/6\n"
    "☎️ Հեռախոս — +374 77 554677 / +374 33 554677\n"
    "💬 Viber • WhatsApp • Telegram — +374 77 554677\n"
    "🕒 Ժամեր — 10:00–02:00 ամեն օր"
)

TAXI_TERMS = (
    "📄 *Տաքսոպարկի պայմանները*\n\n"
    "💰 Միջնորդավճար — *19.4%*\n"
    "🏛 Պետական տուրք — կանխիկ *3.5%*, անկանխիկ *2.5%*\n"
    "💳 Անկանխիկ պատվերները փոխանցվում են մոտ *5 րոպեում*։\n"
    "❌ Թաքնված պահումներ չկան։"
)

TAXI_BONUS = (
    "🎁 *Բոնուսային համակարգ*\n\n"
    "🆕 Նոր վարորդների համար մինչև *20,000 դրամ* բոնուս։\n"
    "📈 Շաբաթական և ամսական բոնուսային համակարգ։\n"
    "🔔 Ծանուցումները հասնում են Յանդեքս Պրո հավելվածում և մեր ալիքներով։"
)

DELIVERY_ABOUT = (
    "📦 *Յանդեքս Գո Առաքում*\n\n"
    "Մենք հանդիսանում ենք Յանդեքս Գո Առաքման պաշտոնական գործընկերը ՀՀ-ում։\n"
    "Աշխատում ենք ավելի քան *12,000 առաքիչների* հետ՝ ապահովելով հուսալի և հարմարավետ պայմաններ։\n\n"
    "📍 Հասցե՝ ք. Երևան, Տիգրան Մեծ 55/6\n"
    "☎️ Հեռախոս՝ +374 77 554677\n"
    "💬 Viber • WhatsApp • Telegram՝ +374 77 554677\n"
    "🕒 Ժամեր՝ 10:00–02:00 ամեն օր"
)

DELIVERY_TERMS_CAR = (
    "🚗 *Մեքենայով և բեռնատարով առաքումներ*\n\n"
    "💰 Միջնորդավճար՝ 26.8%\n"
    "💵 Պատվերները լինում են կանխիկ և անկանխիկ։\n"
    "💳 Անկանխիկ պատվերների գումարները փոխանցվում են Իդրամ հաշվին՝ առավելագույնը 5 րոպեում։\n"
    "❌ Այլ պահումներ և գանձումներ չկան։"
)

DELIVERY_TERMS_MOPED = (
    "🛵 *Մոպեդով և մոտոցիկլով առաքումներ*\n\n"
    "💰 Միջնորդավճար՝ 27%\n"
    "🍔 Հիմնականում կատարվում են սննդի պատվերներ։\n"
    "💸 Առաքիչը պետք է ունենա հաշվեկշռին առնվազն 20,000 դրամ՝ վճարում առաքման պահին տարբերակի համար։\n"
    "🎒 Պարտադիր է ունենալ տերմոպայուսակ։"
)

DELIVERY_TERMS_FOOT = (
    "🚶‍♂️ *Ոտքով առաքումներ*\n\n"
    "💰 Միջնորդավճար՝ 27%\n"
    "🍕 Առաքվում են սննդի պատվերներ և փոքր փաթեթներ։\n"
    "💸 Առաքիչը պետք է ունենա հաշվեկշռին առնվազն 20,000 դրամ՝ վճարում առաքման պահին տարբերակի համար։\n"
    "🎒 Պարտադիր է ունենալ տերմոպայուսակ։"
)

DELIVERY_BONUS = (
    "🎁 *Բոնուսային համակարգ*\n\n"
    "🚗 Մեքենայով և բեռնատարով առաքիչների համար՝ մինչև *15,000 դրամ* բոնուս։\n"
    "🛵 Մոպեդով և ոտքով առաքիչների համար՝ մինչև *10,000 դրամ* բոնուս։\n"
    "📈 Առկա են շաբաթական և ամսական բոնուսային ծրագրեր։"
)

# ======== ՍԿԻԶԲ ========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users = load_users()
    if str(user.id) not in users:
        users[str(user.id)] = {
            "name": user.first_name,
            "username": user.username,
            "joined": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_users(users)
    await update.message.reply_text(
        f"👋 Ողջույն, {user.first_name}!\n\nՄենք հանդիսանում ենք Յանդեքս Գո-ի պաշտոնական գործընկերը ՀՀ-ում։\nԸնտրեք ստորև տարբերակը 👇",
        reply_markup=kb_main()
    )

# ======== ADMIN COMMANDS ========
async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 Ձեր Telegram ID-ն է՝ `{update.effective_user.id}`", parse_mode="Markdown")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Մուտքը միայն ադմինի համար է։")
        return
    users = load_users()
    total = len(users)
    await update.message.reply_text(f"📊 Ընդհանուր օգտատերեր՝ *{total}*", parse_mode="Markdown")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Միայն ադմինը կարող է ուղարկել հաղորդագրություններ։")
        return
    text = " ".join(context.args)
    users = load_users()
    sent = 0
    for uid in users.keys():
        try:
            await context.bot.send_message(chat_id=int(uid), text=text)
            sent += 1
        except:
            pass
    await update.message.reply_text(f"✅ Ուղարկվեց {sent} օգտատերերին։")

# ======== CALLBACK ROUTER ========
# (օգտագործիր վերջին ուղղված տարբերակը այստեղ, որը ես քեզ արդեն տվել էի)

# ======== ԳԼԽԱՎՈՐ ՖՈՒՆԿՑԻԱ ========
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(cb_router))
    print("✅ Y TAXI բոտը աշխատում է...")
    await app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(main())
    loop.run_forever()
