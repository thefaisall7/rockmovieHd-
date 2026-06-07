import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import firebase_admin
from firebase_admin import credentials, db

# --- FIREBASE DATABASE SETUP ---
# Ab hum file read nahi karenge, direct environment variable se data uthayenge
try:
    firebase_key_raw = os.environ.get("FIREBASE_KEY_JSON")
    if firebase_key_raw:
        firebase_info = json.loads(firebase_key_raw)
        cred = credentials.Certificate(firebase_info)
    else:
        # Agar variable nahi mila toh backup ke liye file try karega
        cred = credentials.Certificate('firebase-key.json')
except Exception as e:
    print(f"Firebase key loading error: {e}")
    cred = credentials.Certificate('firebase-key.json')

# Aapka asli Firebase Database URL
FIREBASE_DB_URL = "https://rockmoviehdbot-default-rtdb.asia-southeast1.firebasedatabase.app/"

firebase_admin.initialize_app(cred, {
    'databaseURL': FIREBASE_DB_URL
})

movies_ref = db.reference('movies')

# --- ADMIN CONFIGURATION ---
ADMIN_ID = 5126747940 

# --- BOT COMMAND HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 **Welcome to Rock Movie HD Bot!** 🚀\n\n"
        "Bhai, bas movie ka naam likh kar bhejo, mai aapko download link de dunga!"
    )

async def add_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Arre bhai, aap is bot ke admin nahi ho!")
        return

    if not context.args or "|" not in " ".join(context.args):
        await update.message.reply_text("❌ Sahi format use karo bhai!\nExample: `/add Pushpa 2 | https://link.com`")
        return

    full_text = " ".join(context.args)
    movie_name, movie_link = map(str.strip, full_text.split("|"))
    movie_key = movie_name.lower().replace(".", "_").replace("$", "_").replace("#", "_")
    
    movies_ref.child(movie_key).set({
        "display_name": movie_name,
        "link": movie_link
    })
    await update.message.reply_text(f"✅ **Done Bhai!**\n🎬 Movie: {movie_name}\n🔗 Link: {movie_link}\nDatabase me safe ho gayi hai!")

async def search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.lower().strip()
    movie_key = query.replace(".", "_").replace("$", "_").replace("#", "_")
    movie_data = movies_ref.child(movie_key).get()
    
    if movie_data:
        name = movie_data.get("display_name")
        link = movie_data.get("link")
        await update.message.reply_text(
            f"🎬 **Aapki Movie Mil Gayi Bhai!**\n\n"
            f"🍿 **Name:** {name}\n"
            f"⚡ **HD Quality Link:** {link}\n\n"
            f"Enjoy karo! ❤️ Share zaroor karna."
        )
    else:
        await update.message.reply_text(
            "❌ **Sorry Bhai!** Ye movie abhi mere database me nahi hai.\n\n"
            "Main jald hi ise add kar dunga. Tab tak spelling check kar lo ek baar!"
        )

# --- MAIN RUNNER ---
if __name__ == '__main__':
    # Token direct Render ke environment variable se aayega
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('add', add_movie))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_movie))
    
    print("Bot is rocking and running...")
    app.run_polling()

