import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import firebase_admin
from firebase_admin import credentials, db

# --- FIREBASE DATABASE SETUP ---
# Hamari downloaded json file ko read karega
cred = credentials.Certificate('firebase-key.json')

# Yahan apne Firebase Database ka URL daalein
# (Example: https://your-project-id-default-rtdb.firebaseio.com/)
FIREBASE_DB_URL = os.environ.get("FIREBASE_DB_URL", "APNA_FIREBASE_URL_YAHAN_DALO")

firebase_admin.initialize_app(cred, {
    'databaseURL': FIREBASE_DB_URL
})

# Reference to the movies node in Firebase
movies_ref = db.reference('movies')

# --- ADMIN CONFIGURATION ---
# Apni asli Telegram User ID yahan daalein taaki sirf aap hi movie add kar sakein
ADMIN_ID = int(os.environ.get("ADMIN_ID", 123456789)) 


# --- BOT COMMAND HANDLERS ---

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 **Welcome to Rock Movie HD Bot!** 🚀\n\n"
        "Bhai, bas movie ka naam likh kar bhejo, mai aapko download link de dunga!"
    )

# /add command (Sirf Admin ke liye - Movie add karne ke liye)
# Usage: /add Pushpa 2 | https://teraboxlink.com
async def add_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Arre bhai, aap is bot ke admin nahi ho!")
        return

    # Check input format
    if not context.args or "|" not in " ".join(context.args):
        await update.message.reply_text("❌ Sahi format use karo bhai!\nExample: `/add Pushpa 2 | https://link.com`")
        return

    full_text = " ".join(context.args)
    movie_name, movie_link = map(str.strip, full_text.split("|"))
    
    # Firebase me save karne ke liye name ko lowercase (chote aksharo) me convert karenge
    movie_key = movie_name.lower().replace(".", "_").replace("$", "_").replace("#", "_") # Firebase keys restriction fix
    
    movies_ref.child(movie_key).set({
        "display_name": movie_name,
        "link": movie_link
    })
    
    await update.message.reply_text(f"✅ **Done Bhai!**\n🎬 Movie: {movie_name}\n🔗 Link: {movie_link}\nDatabase me safe ho gayi hai!")

# Movie Search Logic (Jab koi bhi text bhejega)
async def search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.lower().strip()
    
    # Firebase key restrictions ke hisab se clean karo query ko
    movie_key = query.replace(".", "_").replace("$", "_").replace("#", "_")
    
    # Database me check karo
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
    # Koyeb par environment variable se token uthayega
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "APNA_TELEGRAM_TOKEN_YAHAN_DALO")
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Handlers link karo
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('add', add_movie))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_movie))
    
    print("Bot is rocking and running...")
    app.run_polling()
