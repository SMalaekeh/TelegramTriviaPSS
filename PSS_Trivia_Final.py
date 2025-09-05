import logging
import re
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# Designated user (quiz master) ID
DESIGNATED_USER_ID = 71769373

# Define conversation state constants
QUESTION, NEXT = range(2)

# 19 fixed questions (adjust as needed)
questions = [
    {"question": "سوال اول: به نظرت روتین ورزشی اشکان چیه؟", 
     "options": ["پیاده‌روی تا یخچال", "شبا میره یوگا", "عصرا میره استخر", "صبحا میدوئه"], 
     "answer": "صبحا میدوئه"},
    {"question": "سوال دوم: به نظرت یاسمن اگه می‌خواست یه حیوون رو بذاره تو سفره هفت‌سین چی ‌می‌ذاشت؟", 
     "options": ["موش", "سگ", "شامپانزه", "گربه"], 
     "answer": "سگ"},
    {"question": "سوال سوم: به نظرت سپهر حلیم رو با نمک می‌خوره یا شکر؟ کباب رو با دوغ یا نوشابه؟", 
     "options": ["حلیم با نمک - کباب با نوشابه", "حلیم با نمک - کباب با دوغ", "حلیم با شکر - کباب با نوشابه",
                  "حلیم با شکر - کباب با دوغ"], 
     "answer": "حلیم با نمک - کباب با دوغ"},
    {"question": "سوال چهارم: به نظرت کدوم سین سفره هفت‌سین شخصیت نسیم رو نشون میده؟", 
     "options": ["سیر", "سبزه", "سمنو", "سماق"], 
     "answer": "سماق"},
    {"question": "سوال پنجم: به نظر سجاد اگه حاجی فیروز، حاجی نوروز نبود چی کاره‌ می‌شد؟", 
     "options": ["دانشجو دکترا", "دلال", "کمدین", "راننده تاکسی"], 
     "answer": "دانشجو دکترا"},
    {"question": "سوال ششم: به نظرت ملیکا اگه شیرینی عید بود کدوم شیرینی دوست داشت باشه؟", 
     "options": ["پاپیونی", "گردویی", "برنجی", "نخودچی"], 
     "answer": "نخودچی"},
    {"question": "سوال هفتم: به نظرت اگه دانیال می‌تونست یکی از شخصیت‌های شاهنامه باشه کدوم رو انتخاب می‌کرد؟", 
     "options": ["رستم", "سیاوش", "زال", "سهراب"], 
     "answer": "زال"},
    {"question": "سوال هشتم: اگه قرار باشه فوتبال بازی کنیم به نظرت روژین کی رو می‌ذاره دروازه؟", 
     "options": ["نیما رشگی", "اشکان مددی", "علی خانپور", "مهدی اخباری"], 
     "answer": "علی خانپور"},
    {"question": "سوال نهم: به نظرت اگه علی خانپور آجیل می‌بود، چی می‌بود؟", 
     "options": ["نخودچی کشمش", "فندق", "پسته", "بادوم هندی"], 
     "answer": "فندق"},
    {"question": "سوال دهم: به نظرت اگه محمدرضا یه شخصیت کارتونی بود، چی می‌بود؟", 
     "options": ["تام (از تام و جری)", "باب اسفنجی", "گارفیلد", "پاندای کنگفوکار"], 
     "answer": "پاندای کنگفوکار"},
    {"question": "سوال یازدهم: جونم بسته به جونت جونمی", 
     "options": ["شعله‌ی سرخ این قلب دیوونمی", "شعله‌های داغ این دل مجنونمی", "خون تو رگ این دل مجنونمی", "چشمات مثل ماهه روشنمی"], 
     "answer": "خون تو رگ این دل مجنونمی"},
    {"question": "سوال دوازدهم: دختر ----- و ببین لباش گل اناره ///// از سر تا پای ناز اون عشق و صفا می‌باره", 
     "options": ["گیلانو", "تهرونو", "شیرازو", "اصفهونو"], 
     "answer": "گیلانو"},
    {"question": "سوال سیزدهم: اسم پسر هاشم آقا؟", 
     "options": ["محمد", "علی", "عباس", "سعید"], 
     "answer": "سعید"},
    {"question": "سوال چهاردهم: همسایه حبیب فامیلش چی بود؟", 
     "options": ["آقای امیری", "آقای شریفی", "آقای مهاجر", "هیچکدام"], 
     "answer": "آقای امیری"},
    {"question": "سوال پانزدهم: اولین پادشاه ایرانی که نوروز را جشن گرفت؟", 
     "options": ["داریوش اول", "کوروش", "انوشیروان دادگر", "جمشید"], 
     "answer": "جمشید"},
    {"question": "سوال شانزدهم: کار هستی گاه بردن شد زمانی باختن ///// گه بپیچاند گوشت، گه دهندت گوشوار", 
     "options": ["پروین اعتصامی", "احمد شاملو", "محمدتقی بهار", "حسین منزوی"], 
     "answer": "پروین اعتصامی"},
    {"question": "سوال هفدهم: آقا بهمن چه سالی طرفدار نمونه پرسپولیس شده است؟", 
     "options": ["سال ۹۲", "سال ۹۴", "سال ۹۶", "سال ۹۸"], 
     "answer": "سال ۹۴"},
    {"question": "سوال هجدهم: حاج آقا چند سال تو اون محله زندگی می‌کرد؟", 
     "options": ["۱۴", "۲۴", "۳۴", "۴۴"], 
     "answer": "۲۴"},
    {"question": "سوالا چطور بود؟", 
     "options": ["عالی", "خوب", "قابل قبول", "نیاز به تلاش بیشتری"], 
     "answer": "تموم کردیم!"}
]

# Global dictionaries for user progress, responses, and overall scoreboard
user_scores = {}   # Stores each user's score, current question index, and individual responses
scoreboard = {}    # Stores each user's final score
# Global dictionary to store aggregate responses for each question (indexed 0 to len(questions)-1)
aggregate_results = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    # Initialize user data including responses list
    user_scores[user_id] = {"score": 0, "question_index": 0, "responses": []}
    await update.message.reply_text("به مهمونی امشب خوش اومدید! ۱۹ تا سوال داریم که یکی یکی می‌ریم جلو! لطفا صبر کنید که همه جواب بدهند و بعد با هم بریم سوال بعدی.")
    return await ask_question(update, context)

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    index = user_scores[user_id]["question_index"]
    
    # If all questions have been asked, end the quiz
    if index >= len(questions):
        return await end_quiz(update, context)
    
    current_question = questions[index]
    keyboard = [[option] for option in current_question["options"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    
    await update.message.reply_text(current_question["question"], reply_markup=reply_markup)
    return QUESTION

async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_answer = update.message.text
    index = user_scores[user_id]["question_index"]
    correct_answer = questions[index]["answer"]
    
    # Save the user's answer with the correct answer in their session
    user_scores[user_id]["responses"].append({
        "question": questions[index]["question"],
        "user_answer": user_answer,
        "correct_answer": correct_answer
    })
    
    # Update the user's score: for the last question, any answer is correct.
    if index == len(questions) - 1:
        user_scores[user_id]["score"] += 1
    else:
        if user_answer == correct_answer:
            user_scores[user_id]["score"] += 1
    
    # --- Update aggregate results ---
    # Initialize the aggregate_results for this question if not already done.
    if index not in aggregate_results:
        aggregate_results[index] = {}
    # Increase count for the given answer
    aggregate_results[index][user_answer] = aggregate_results[index].get(user_answer, 0) + 1
    
    # Prompt the user to press 'Next' to continue
    keyboard = [["هروقت میزبان گفت بریم سوال بعدی، لطفا اینجا کلیک کنید."]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("جوابت ثبت شد، لطفا صبر کنید تا ببینیم جواب درست چیه!", reply_markup=reply_markup)
    return NEXT

async def next_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    # Increment question index and show next question (or finish if done)
    user_scores[user_id]["question_index"] += 1
    return await ask_question(update, context)

async def end_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    score = user_scores[user_id]["score"]
    username = update.effective_user.first_name
    final_message = f"Quiz finished! Your score is {score} out of {len(questions)}.\n\n"
    final_message += "جوابای درست:\n\n"
    
    for idx, response in enumerate(user_scores[user_id]["responses"], start=1):
        final_message += (
            f"سوال {idx}: {response['question']}\n"
            f"جواب شما: {response['user_answer']}\n"
            f"جواب درست: {response['correct_answer']}\n\n"
        )
    
    await update.message.reply_text(final_message)
    scoreboard[user_id] = (username, score)
    await show_scoreboard(update, context)
    return ConversationHandler.END

async def show_scoreboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not scoreboard:
        await update.message.reply_text("!هیچی فعلا نیست")
        return
    
    sorted_scores = sorted(scoreboard.items(), key=lambda item: item[1][1], reverse=True)
    scoreboard_text = "🏆 Leaderboard:\n"
    for rank, (uid, (name, score)) in enumerate(sorted_scores, start=1):
        scoreboard_text += f"{rank}. {name}: {score}\n"
    
    await update.message.reply_text(scoreboard_text)

async def scoreboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not scoreboard:
        await update.message.reply_text("!هیچی فعلا نیست")
    else:
        sorted_scores = sorted(scoreboard.items(), key=lambda item: item[1][1], reverse=True)
        scoreboard_text = "🏆 Leaderboard:\n"
        for rank, (uid, (name, score)) in enumerate(sorted_scores, start=1):
            scoreboard_text += f"{rank}. {name}: {score}\n"
        await update.message.reply_text(scoreboard_text)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Only allow the designated user to use reset
    if update.effective_user.id != DESIGNATED_USER_ID:
        await update.message.reply_text("شما اجازه استفاده از این دستور رو ندارید!")
        return
    user_scores.clear()
    scoreboard.clear()
    aggregate_results.clear()
    await update.message.reply_text("All questions and scores have been reset!")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Quiz cancelled.")
    return ConversationHandler.END

async def result_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # This handler is only accessible by the designated user.
    if update.effective_user.id != DESIGNATED_USER_ID:
        return
    command_text = update.message.text  # e.g. "/result3"
    m = re.search(r'/result(\d+)', command_text)
    if not m:
        await update.message.reply_text("دستور نامعتبر است.")
        return
    question_number = int(m.group(1))
    if question_number < 1 or question_number > len(questions):
        await update.message.reply_text("شماره سوال نامعتبر است.")
        return
    q_index = question_number - 1
    if q_index not in aggregate_results or not aggregate_results[q_index]:
        await update.message.reply_text("برای این سوال هنوز جوابی ثبت نشده.")
        return
    total = sum(aggregate_results[q_index].values())
    response_text = f"نتایج سوال {question_number}:\n"
    # Loop over the defined options for the question to maintain order.
    for option in questions[q_index]["options"]:
        count = aggregate_results[q_index].get(option, 0)
        percentage = (count / total) * 100 if total > 0 else 0
        response_text += f"{option}: {count} پاسخ ({percentage:.1f}%)\n"
    await update.message.reply_text(response_text)

def main():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    app = ApplicationBuilder().token("7284341616:AAGtGSDW2zguWIOk5dfVDock09RV6kdMdAI").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer)],
            NEXT: [MessageHandler(filters.Regex('^هروقت میزبان گفت بریم سوال بعدی، لطفا اینجا کلیک کنید.$'), next_question)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("scoreboard", scoreboard_command))
    # Reset command available only to the designated user.
    app.add_handler(CommandHandler("reset", reset, filters=filters.User(user_id=DESIGNATED_USER_ID)))
    # Add a result handler: commands like /result1, /result2, ..., /result19 (accessible only by the designated user)
    app.add_handler(MessageHandler(filters.Regex(r'^/result\d+$') & filters.User(user_id=DESIGNATED_USER_ID), result_handler))
    
    app.run_polling()

if __name__ == '__main__':
    main()
