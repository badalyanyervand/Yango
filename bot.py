# -*- coding: utf-8 -*-
import asyncio
import nest_asyncio
import telegram
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ======== CONFIG ========
BOT_TOKEN = "ԱՅՍՏԵՂ_ԴԻՐ_ՔՈ_TOKENԸ"   # օրինակ՝ "8473629116:AAHmkdxdxnAmW58KQaZdE2eC05rwsmUI4wE"
TELEGRAM_USERNAME = "yandexgopartner"
PHONE = "+37477554677"
FORM_URL = "https://forms.gle/tKVJgHu1KCNZhCvRA"

# HTTP սխալի ուղղում
telegram.request._baserequest._DEFAULT_HTTP_IMPL = "httpx"

# nest_asyncio ֆիքս event loop-ի համար
nest_asyncio.apply()

# ======== ՕԳՏԱԿԱՐ ԿՈՃԱԿՆԵՐ ========
def kb_back_and_call(back_data: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Գրիր Telegram-ում", url=f"https://t.me/{TELEGRAM_USERNAME}")],
        [
            InlineKeyboardButton("📞 WhatsApp", url=f"https://wa.me/{PHONE.replace('+','')}"),
            InlineKeyboardButton("📱 Զանգ (WhatsApp)", url=f"https://wa.me/{PHONE.replace('+','')}")
        ],
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
    "Մենք հանդիսանում ենք *Յանդեքս Գո* ծառայության գործընկերը Հայաստանում 2017թ-ից, "
    "և մեզ հետ համագործակցում են ավելի քան *10,000 վարորդներ*։\n\n"
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

# ======== ՍԿԶԲ ====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name or "օգտատեր"
    await update.message.reply_text(
        f"👋 Ողջույն, {user}!\n\nՄենք հանդիսանում ենք Յանդեքս Գո-ի պաշտոնական գործընկերը ՀՀ-ում։\nԸնտրեք ստորև տարբերակը 👇",
        reply_markup=kb_main()
    )

# ======== CALLBACK ROUTER ========
async def cb_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    await q.answer()

    if data == "main":
        await q.edit_message_text("Ընտրեք տարբերակը 👇", reply_markup=kb_main()); return
    if data == "existing":
        await q.edit_message_text("Շնորհակալություն վստահության համար ❤️", reply_markup=kb_back_and_call("main")); return
    if data == "partner":
        await q.edit_message_text("Ընտրեք համագործակցության ոլորտը 👇", reply_markup=kb_partner_areas()); return
    if data == "taxi":
        await q.edit_message_text("🚖 *Տաքսի բաժին*\nԸնտրեք ենթակետ 👇", reply_markup=kb_taxi_menu(), parse_mode="Markdown"); return
    if data == "taxi_about":
        await q.edit_message_text(TAXI_ABOUT, parse_mode="Markdown", reply_markup=kb_back_and_call("taxi")); return
    if data == "taxi_terms":
        await q.edit_message_text(TAXI_TERMS, parse_mode="Markdown", reply_markup=kb_back_and_call("taxi")); return
    if data == "taxi_bonus":
        await q.edit_message_text(TAXI_BONUS, parse_mode="Markdown", reply_markup=kb_back_and_call("taxi")); return
    if data == "taxi_partner":
        await q.edit_message_text(
            "🤝 **Ուրախ ենք, որ ցանկանում եք դառնալ մեր գործընկերը։**\n\nՇնորհակալ ենք, որ ընտրել և վստահել եք մեզ։\n"
            f"📋 [Լրացնել գրանցման ձևը]({FORM_URL})",
            parse_mode="Markdown", reply_markup=kb_back_and_call("taxi")
        ); return

    if data == "delivery":
        await q.edit_message_text("📦 *Առաքման ձևեր*\nԸնտրեք 👇", reply_markup=kb_delivery_menu_root(), parse_mode="Markdown"); return

    if data in ("delivery_car", "delivery_moped", "delivery_foot", "delivery_truck"):
        names = {
            "delivery_car": "🚗 Մեքենայով առաքումներ",
            "delivery_moped": "🛵 Մոպեդով առաքումներ",
            "delivery_foot": "🚶‍♂️ Ոտքով առաքումներ",
            "delivery_truck": "🚛 Բեռնատարով առաքումներ"
        }
        await q.edit_message_text(f"{names[data]}\nԸնտրեք ենթակետ 👇", reply_markup=kb_delivery_section(data)); return

    if data.endswith("_partner"):
        await q.edit_message_text(
            "🤝 **Ուրախ ենք, որ ցանկանում եք դառնալ մեր գործընկերը։**\n\nՇնորհակալ ենք, որ ընտրել և վստահել եք մեզ։\n"
            f"📋 [Լրացնել գրանցման ձևը]({FORM_URL})",
            parse_mode="Markdown", reply_markup=kb_back_and_call("delivery")
        ); return

# ======== ԳԼԽԱՎՈՐ ԱՍԻՆԽՐՈՆ ՖՈՒՆԿՑԻԱ ========
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(cb_router))
    print("✅ Y TAXI բոտը աշխատում է...")
    await app.run_polling(drop_pending_updates=True)

# ======== ԳՈՐԾԱՐԿՈՒՄ (macOS-safe) ========
if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(main())
    loop.run_forever()
