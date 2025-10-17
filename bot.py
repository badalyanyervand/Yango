# -*- coding: utf-8 -*-
import asyncio
import nest_asyncio
import telegram
import os
import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

# ====== LOGGING ======
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
log = logging.getLogger("Y-TAXI")

# ====== CONFIG ======
BOT_TOKEN = os.getenv("BOT_TOKEN", "8473629116:AAHmkdxdxnAmW58KQaZdE2eC05rwsmUI4wE")
TELEGRAM_USERNAME = "yandexgopartner"
PHONE = "+37477554677"
FORM_URL = "https://forms.gle/tKVJgHu1KCNZhCvRA"
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))  # ⚠️ դիր քոնը կամ փոխանցիր ENV-ով

# HTTP impl fix՝ macOS/Render համատեղելիության համար
telegram.request._baserequest._DEFAULT_HTTP_IMPL = "httpx"
nest_asyncio.apply()

USERS_FILE = "users.json"
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# ====== KEYBOARDS ======
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
    # prefix: delivery_car | delivery_moped | delivery_foot | delivery_truck
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💛 Մեր մասին", callback_data=f"{prefix}_about")],
        [InlineKeyboardButton("📄 Պայմաններ", callback_data=f"{prefix}_terms")],
        [InlineKeyboardButton("🎁 Բոնուսային համակարգ", callback_data=f"{prefix}_bonus")],
        [InlineKeyboardButton("🤝 Դառնալ գործընկեր", callback_data=f"{prefix}_partner")],
        [InlineKeyboardButton("⬅️ Հետ գնալ", callback_data="delivery")]
    ])

# ====== TEXTS ======
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
    "💵 Պատվերներ՝ կանխիկ և անկանխիկ\n"
    "💳 Անկանխիկ պատվերների գումարները փոխանցվում են Իդրամ հաշվին՝ առավելագույնը 5 րոպեում\n"
    "❌ Այլ պահումներ և գանձումներ չկան"
)

DELIVERY_TERMS_MOPED = (
    "🛵 *Մոպեդով/մոտոցիկլով առաքումներ*\n\n"
    "💰 Միջնորդավճար՝ 27%\n"
    "🍔 Հիմնականում սննդի պատվերներ\n"
    "💸 Խորհուրդ է տրվում հաշվեկշռին ունենալ ≥ 20,000 դրամ (վճարում առաքման պահին տարբերակ)\n"
    "🎒 Պարտադիր՝ տերմոպայուսակ"
)

DELIVERY_TERMS_FOOT = (
    "🚶‍♂️ *Ոտքով առաքումներ*\n\n"
    "💰 Միջնորդավճար՝ 27%\n"
    "🍕 Սննդի պատվերներ և փոքր փաթեթներ\n"
    "💸 Խորհուրդ է տրվում հաշվեկշռին ունենալ ≥ 20,000 դրամ (վճարում առաքման պահին տարբերակ)\n"
    "🎒 Պարտադիր՝ տերմոպայուսակ"
)

DELIVERY_BONUS = (
    "🎁 *Բոնուսային համակարգ*\n\n"
    "🚗 Մեքենայով/բեռնատարով՝ մինչև *15,000 դրամ* բոնուս\n"
    "🛵 Մոպեդով/🚶‍♂️ ոտքով՝ մինչև *10,000 դրամ* բոնուս\n"
    "📈 Շաբաթական և ամսական ծրագրեր"
)

# ====== START & ADMIN ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # save user
    users = load_users()
    if str(user.id) not in users:
        users[str(user.id)] = {
            "name": user.first_name,
            "username": user.username,
            "joined": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_users(users)
        log.info(f"New user: {user.id} | {user.first_name} | @{user.username}")

    await update.message.reply_text(
        f"👋 Ողջույն, {user.first_name or 'օգտատեր'}!\n\n"
        "Մենք հանդիսանում ենք Յանդեքս Գո-ի պաշտոնական գործընկերը ՀՀ-ում։\n"
        "Ընտրեք ստորև տարբերակը 👇",
        reply_markup=kb_main()
    )

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 {update.effective_user.id}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 Միայն ադմինին է հասանելի։")
    users = load_users()
    await update.message.reply_text(f"📊 Ընդհանուր օգտատերեր՝ *{len(users)}*", parse_mode="Markdown")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 Միայն ադմինը կարող է ուղարկել։")
    text = " ".join(context.args) or "(դատարկ հաղորդագրություն)"
    users = load_users()
    sent = 0
    for uid in list(users.keys()):
        try:
            await context.bot.send_message(int(uid), text)
            sent += 1
        except Exception as e:
            log.warning(f"Broadcast to {uid} failed: {e}")
    await update.message.reply_text(f"✅ Ուղարկվեց {sent} օգտատերերի։")

# ====== CALLBACK ROUTER (ուղղված հերթականությամբ) ======
async def cb_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    log.info(f"Callback data: {data}")  # DEBUG լոգ — տեսնելու, թե ինչ է գալիս
    await q.answer()

    # 0) Գլխավոր վերադարձ
    if data == "main":
        return await q.edit_message_text("Ընտրեք տարբերակը 👇", reply_markup=kb_main())

    # 1) «Արդեն համագործակցում եմ»
    if data == "existing":
        return await q.edit_message_text(
            "Շնորհակալություն վստահության համար ❤️",
            reply_markup=kb_back_and_call("main")
        )

    # 2) «Ցանկանում եմ համագործակցել»
    if data == "partner":
        return await q.edit_message_text("Ընտրեք համագործակցության ոլորտը 👇", reply_markup=kb_partner_areas())

    # 3) Տաքսի՝ արմատ մենյու
    if data == "taxi":
        return await q.edit_message_text(
            "🚖 *Տաքսի բաժին*\nԸնտրեք ենթակետ 👇",
            parse_mode="Markdown",
            reply_markup=kb_taxi_menu()
        )

    # 4) Տաքսի ենթակետեր
    if data == "taxi_about":
        return await q.edit_message_text(TAXI_ABOUT, parse_mode="Markdown", reply_markup=kb_back_and_call("taxi"))
    if data == "taxi_terms":
        return await q.edit_message_text(TAXI_TERMS, parse_mode="Markdown", reply_markup=kb_back_and_call("taxi"))
    if data == "taxi_bonus":
        return await q.edit_message_text(TAXI_BONUS, parse_mode="Markdown", reply_markup=kb_back_and_call("taxi"))
    if data == "taxi_partner":
        return await q.edit_message_text(
            "🤝 **Ուրախ ենք, որ ցանկանում եք դառնալ մեր գործընկերը։**\n\n"
            "Շնորհակալ ենք, որ ընտրել և վստահել եք մեզ։\n"
            f"📋 [Լրացնել գրանցման ձևը]({FORM_URL})",
            parse_mode="Markdown",
            reply_markup=kb_back_and_call("taxi")
        )

    # 5) Առաքում՝ արմատ մենյու
    if data == "delivery":
        return await q.edit_message_text(
            "📦 *Առաքման ձևեր*\nԸնտրեք 👇",
            parse_mode="Markdown",
            reply_markup=kb_delivery_menu_root()
        )

    # 6) Առաքում ենթաբաժին ընտրելիս՝ ցույց է տալիս ենթակոճակները
    if data in ("delivery_car", "delivery_moped", "delivery_foot", "delivery_truck"):
        return await q.edit_message_text(
            "Ընտրեք ենթակետ 👇",
            reply_markup=kb_delivery_section(data)
        )

    # ⚠️ ԿՐԻՏԻԿԱԿԱՆ — ԵՆԹԱԿԵՏԵՐԻ ՃՇԳՐԻՏ ՊԱՅՄԱՆՆԵՐԸ
    # 7) Առաքում — Մեր մասին
    if data.endswith("_about"):
        return await q.edit_message_text(
            DELIVERY_ABOUT,
            parse_mode="Markdown",
            reply_markup=kb_back_and_call("delivery")
        )

    # 8) Առաքում — Պայմաններ
    if data.endswith("_terms"):
        if "car" in data or "truck" in data:
            text = DELIVERY_TERMS_CAR
        elif "moped" in data:
            text = DELIVERY_TERMS_MOPED
        elif "foot" in data:
            text = DELIVERY_TERMS_FOOT
        else:
            text = "Պայմանների տվյալներ բացակայում են։"
        return await q.edit_message_text(text, parse_mode="Markdown", reply_markup=kb_back_and_call("delivery"))

    # 9) Առաքում — Բոնուս
    if data.endswith("_bonus"):
        return await q.edit_message_text(
            DELIVERY_BONUS, parse_mode="Markdown", reply_markup=kb_back_and_call("delivery")
        )

    # 10) Առաքում — Դառնալ գործընկեր
    if data.endswith("_partner"):
        return await q.edit_message_text(
            "🤝 **Ուրախ ենք, որ ցանկանում եք դառնալ մեր գործընկերը։**\n\n"
            "Շնորհակալ ենք, որ ընտրել և վստահել եք մեզ։\n"
            f"📋 [Լրացնել գրանցման ձևը]({FORM_URL})",
            parse_mode="Markdown",
            reply_markup=kb_back_and_call("delivery")
        )

    # Անճանաչ callback → վերադարձ հիմնական
    return await q.edit_message_text("Ընտրեք տարբերակը 👇", reply_markup=kb_main())

# ====== APP ======
async def main():
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .concurrent_updates(False)  # կանխում է race condition-ները
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(cb_router))

    log.info("✅ Y TAXI բոտը աշխատում է...")
    await app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    # macOS / Python 3.15 ապահով loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(main())
    loop.run_forever()
