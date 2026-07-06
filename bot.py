import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN")

# Conversation states
MENU, GET_INGREDIENTS, GET_BUDGET, GET_CYCLE, GET_GOAL, GET_HEIGHT, GET_WEIGHT = range(7)

# Meal database — prices updated to reflect 2026 Nigerian market rates
MEALS = [
    {"name": "Jollof Rice & Egg", "cost": 1800, "calories": 520, "protein": 18, "carbs": 65, "fats": 12, "ingredients": ["rice", "egg", "tomato", "onion"]},
    {"name": "Beans & Plantain", "cost": 1500, "calories": 480, "protein": 22, "carbs": 58, "fats": 8, "ingredients": ["beans", "plantain"]},
    {"name": "Egg Sauce & Bread", "cost": 1000, "calories": 410, "protein": 16, "carbs": 48, "fats": 14, "ingredients": ["egg", "tomato", "onion", "bread"]},
    {"name": "Noodles & Vegetables", "cost": 800, "calories": 380, "protein": 10, "carbs": 55, "fats": 9, "ingredients": ["noodles", "carrot", "onion"]},
    {"name": "Fried Rice & Chicken", "cost": 3500, "calories": 620, "protein": 35, "carbs": 70, "fats": 18, "ingredients": ["rice", "chicken", "carrot", "onion"]},
    {"name": "Akara & Pap", "cost": 700, "calories": 340, "protein": 14, "carbs": 42, "fats": 10, "ingredients": ["beans", "onion", "pepper"]},
    {"name": "Egusi Soup & Eba", "cost": 2500, "calories": 610, "protein": 28, "carbs": 60, "fats": 22, "ingredients": ["egusi", "palm oil", "onion"]},
    {"name": "Spaghetti Jollof", "cost": 1500, "calories": 490, "protein": 12, "carbs": 72, "fats": 11, "ingredients": ["spaghetti", "tomato", "onion"]},
    {"name": "Yam & Egg Sauce", "cost": 2000, "calories": 520, "protein": 15, "carbs": 68, "fats": 13, "ingredients": ["yam", "egg", "tomato"]},
    {"name": "Rice & Stew", "cost": 1800, "calories": 540, "protein": 14, "carbs": 72, "fats": 15, "ingredients": ["rice", "tomato", "onion", "palm oil"]},
    {"name": "Garri & Groundnut", "cost": 600, "calories": 420, "protein": 12, "carbs": 68, "fats": 14, "ingredients": ["garri", "groundnut"]},
    {"name": "Moi Moi & Pap", "cost": 900, "calories": 390, "protein": 18, "carbs": 50, "fats": 8, "ingredients": ["beans", "onion", "pepper", "egg"]},
    {"name": "Indomie & Egg", "cost": 900, "calories": 400, "protein": 14, "carbs": 58, "fats": 13, "ingredients": ["noodles", "egg", "onion"]},
    {"name": "Ofada Rice & Stew", "cost": 2200, "calories": 580, "protein": 16, "carbs": 74, "fats": 17, "ingredients": ["rice", "palm oil", "pepper", "onion"]},
    {"name": "Boiled Yam & Sauce", "cost": 1800, "calories": 500, "protein": 10, "carbs": 72, "fats": 10, "ingredients": ["yam", "tomato", "onion", "palm oil"]},
]


def get_main_menu():
    keyboard = [
        [KeyboardButton("🍽️ Get Meal Suggestions")],
        [KeyboardButton("💰 Check Budget"), KeyboardButton("🥗 Nutrition Info")],
        [KeyboardButton("⚙️ Update Profile"), KeyboardButton("ℹ️ Help")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🥗 *Welcome to Student Meals!*\n\n"
        "I help students eat well on a budget.\n\n"
        "Tell me your ingredients and budget — I will suggest the best meals for you!\n\n"
        "Let's start by setting up your profile.\n\n"
        "*What is your body goal?*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            [
                [KeyboardButton("🏃 Lose Weight"), KeyboardButton("💪 Gain Weight")],
                [KeyboardButton("🧘 Maintain Shape"), KeyboardButton("🏋️ Build Muscle")],
            ],
            resize_keyboard=True,
        ),
    )
    return GET_GOAL


async def get_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["goal"] = update.message.text
    await update.message.reply_text(
        "Got it! 💪\n\nWhat is your *height* in cm?\n\nExample: *165*",
        parse_mode="Markdown",
    )
    return GET_HEIGHT


async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        height = int(update.message.text.strip())
        if height < 100 or height > 250:
            raise ValueError
        context.user_data["height"] = height
        await update.message.reply_text(
            "Great! Now what is your *weight* in kg?\n\nExample: *62*",
            parse_mode="Markdown",
        )
        return GET_WEIGHT
    except ValueError:
        await update.message.reply_text(
            "⚠️ Please enter a valid height in cm (e.g. 165)"
        )
        return GET_HEIGHT


async def get_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        weight = int(update.message.text.strip())
        if weight < 20 or weight > 300:
            raise ValueError
        context.user_data["weight"] = weight
        await update.message.reply_text(
            "Almost done! Is your food allowance *weekly* or *monthly?*",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(
                [
                    [KeyboardButton("📅 Weekly"), KeyboardButton("🗓️ Monthly")],
                ],
                resize_keyboard=True,
            ),
        )
        return GET_CYCLE
    except ValueError:
        await update.message.reply_text(
            "⚠️ Please enter a valid weight in kg (e.g. 62)"
        )
        return GET_WEIGHT


async def get_cycle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "Weekly" in text:
        context.user_data["cycle"] = "Weekly"
    elif "Monthly" in text:
        context.user_data["cycle"] = "Monthly"
    else:
        await update.message.reply_text(
            "Please tap *Weekly* or *Monthly*",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("📅 Weekly"), KeyboardButton("🗓️ Monthly")]],
                resize_keyboard=True,
            ),
        )
        return GET_CYCLE

    await update.message.reply_text(
        f"How much is your *{context.user_data['cycle'].lower()}* food budget?\n\n"
        "Enter amount in ₦\n\n"
        "💡 Examples:\n"
        "Weekly: *15000* – *30000*\n"
        "Monthly: *50000* – *100000*",
        parse_mode="Markdown",
    )
    return GET_BUDGET


async def get_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        budget = int(update.message.text.strip().replace(",", "").replace("₦", ""))
        if budget <= 0:
            raise ValueError
        context.user_data["budget"] = budget
        context.user_data["spent"] = 0
        context.user_data["history"] = []

        await update.message.reply_text(
            f"✅ *Profile set up successfully!*\n\n"
            f"🎯 Goal: {context.user_data.get('goal')}\n"
            f"📏 Height: {context.user_data.get('height')} cm\n"
            f"⚖️ Weight: {context.user_data.get('weight')} kg\n"
            f"💰 Budget: ₦{budget:,} {context.user_data.get('cycle')}\n\n"
            f"You are all set! Tap *Get Meal Suggestions* to start 🍛",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )
        return MENU
    except ValueError:
        await update.message.reply_text(
            "⚠️ Please enter a valid amount in ₦ (e.g. 15000)"
        )
        return GET_BUDGET


async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "Meal Suggestions" in text:
        await update.message.reply_text(
            "🥘 *What ingredients do you have?*\n\n"
            "List them separated by commas:\n\n"
            "Example: *rice, egg, tomato, onion*",
            parse_mode="Markdown",
        )
        return GET_INGREDIENTS

    elif "Check Budget" in text:
        budget = context.user_data.get("budget", 0)
        spent = context.user_data.get("spent", 0)
        remaining = budget - spent
        cycle = context.user_data.get("cycle", "Weekly")
        pct = int((spent / budget) * 100) if budget > 0 else 0
        filled = min(10, pct // 10)
        bar = "🟩" * filled + "⬜" * (10 - filled)

        history = context.user_data.get("history", [])
        history_text = ""
        if history:
            history_text = "\n\n📋 *Recent meals:*\n" + "\n".join(
                [f"• {h['name']} — ₦{h['cost']:,}" for h in history[-5:]]
            )

        status = "⚠️ You are spending fast! Try cheaper meals." if pct > 70 else "👍 You are on track!"

        await update.message.reply_text(
            f"💰 *Budget Overview*\n\n"
            f"{bar} {pct}% used\n\n"
            f"💵 Total: ₦{budget:,} {cycle}\n"
            f"💸 Spent: ₦{spent:,}\n"
            f"✅ Remaining: ₦{remaining:,}\n\n"
            f"{status}"
            f"{history_text}",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )
        return MENU

    elif "Nutrition Info" in text:
        goal = context.user_data.get("goal", "🧘 Maintain Shape")
        weight = context.user_data.get("weight", 60)

        if "Lose" in goal:
            calories = weight * 28
            protein = weight * 1.8
            tip = "Focus on high protein, low carb meals like beans, eggs and fish."
        elif "Gain" in goal or "Muscle" in goal:
            calories = weight * 38
            protein = weight * 2.2
            tip = "Eat calorie-dense meals like eba, rice with protein like chicken and fish."
        else:
            calories = weight * 33
            protein = weight * 1.5
            tip = "Balance your meals with carbs, protein and vegetables daily."

        await update.message.reply_text(
            f"🥗 *Your Daily Nutrition Targets*\n\n"
            f"🎯 Goal: {goal}\n"
            f"⚖️ Weight: {weight} kg\n"
            f"🔥 Daily calories: *{int(calories)} kcal*\n"
            f"💪 Daily protein: *{int(protein)}g*\n\n"
            f"💡 *Tip:* {tip}",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )
        return MENU

    elif "Update Profile" in text:
        context.user_data.clear()
        await update.message.reply_text(
            "Let's update your profile.\n\n*What is your body goal?*",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(
                [
                    [KeyboardButton("🏃 Lose Weight"), KeyboardButton("💪 Gain Weight")],
                    [KeyboardButton("🧘 Maintain Shape"), KeyboardButton("🏋️ Build Muscle")],
                ],
                resize_keyboard=True,
            ),
        )
        return GET_GOAL

    elif "Help" in text:
        await update.message.reply_text(
            "ℹ️ *How to use Student Meals Bot*\n\n"
            "🍽️ *Get Meal Suggestions*\n"
            "Tell me your ingredients and I suggest affordable meals that fit your budget\n\n"
            "💰 *Check Budget*\n"
            "See how much you have spent and how much is left\n\n"
            "🥗 *Nutrition Info*\n"
            "See your daily calorie and protein targets based on your body goal\n\n"
            "⚙️ *Update Profile*\n"
            "Change your goal, height, weight or budget\n\n"
            "💡 *Tip:* After getting meal suggestions, type the meal name to log it and deduct from your budget!",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )
        return MENU

    else:
        suggestions = context.user_data.get("last_suggestions", [])
        for meal in suggestions:
            if meal["name"].lower() in text.lower():
                spent = context.user_data.get("spent", 0)
                budget = context.user_data.get("budget", 0)
                context.user_data["spent"] = spent + meal["cost"]
                history = context.user_data.get("history", [])
                history.append({"name": meal["name"], "cost": meal["cost"]})
                context.user_data["history"] = history
                remaining = budget - context.user_data["spent"]

                await update.message.reply_text(
                    f"✅ *{meal['name']}* logged!\n\n"
                    f"💸 Cost: ₦{meal['cost']:,}\n"
                    f"💰 Budget remaining: ₦{remaining:,}\n"
                    f"🔥 Calories: {meal['calories']} kcal\n"
                    f"💪 Protein: {meal['protein']}g",
                    parse_mode="Markdown",
                    reply_markup=get_main_menu(),
                )
                return MENU

        await update.message.reply_text(
            "Please use the menu buttons below 👇",
            reply_markup=get_main_menu(),
        )
        return MENU


async def get_ingredients(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ingredients_input = update.message.text.lower().strip()
    user_ingredients = [i.strip() for i in ingredients_input.split(",")]

    budget = context.user_data.get("budget", 0)
    spent = context.user_data.get("spent", 0)
    remaining = budget - spent

    matched = []
    partial = []

    for meal in MEALS:
        if meal["cost"] > remaining:
            continue
        match_count = sum(
            1 for ing in meal["ingredients"]
            if any(ui in ing or ing in ui for ui in user_ingredients)
        )
        if match_count == len(meal["ingredients"]):
            matched.append((meal, match_count))
        elif match_count > 0:
            partial.append((meal, match_count))

    matched.sort(key=lambda x: x[1], reverse=True)
    partial.sort(key=lambda x: x[1], reverse=True)

    response = f"🍽️ *Meal Suggestions*\n💰 Budget remaining: ₦{remaining:,}\n\n"

    if matched:
        response += "✅ *You can make right now:*\n"
        for meal, _ in matched[:3]:
            response += (
                f"\n🍛 *{meal['name']}*\n"
                f"💰 ₦{meal['cost']:,} | 🔥 {meal['calories']} kcal | 💪 {meal['protein']}g protein\n"
            )

    if partial:
        response += "\n\n🛒 *Buy a few more items:*\n"
        for meal, _ in partial[:2]:
            missing = [
                ing for ing in meal["ingredients"]
                if not any(ui in ing or ing in ui for ui in user_ingredients)
            ]
            response += (
                f"\n🍲 *{meal['name']}*\n"
                f"💰 ₦{meal['cost']:,} | 🔥 {meal['calories']} kcal\n"
                f"🛒 Still need: {', '.join(missing)}\n"
            )

    if not matched and not partial:
        response += (
            "😕 No meals found for your ingredients and budget.\n\n"
            "Try adding more ingredients like:\n"
            "rice, egg, tomato, onion, beans, plantain, noodles"
        )
    else:
        response += "\n\n💡 *Type a meal name to log it and deduct from your budget!*"

    context.user_data["last_suggestions"] = (
        [m[0] for m in matched[:3]] + [m[0] for m in partial[:2]]
    )

    await update.message.reply_text(
        response, parse_mode="Markdown", reply_markup=get_main_menu()
    )
    return MENU


def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN environment variable not set!")

    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GET_GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_goal)],
            GET_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_height)],
            GET_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_weight)],
            GET_CYCLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_cycle)],
            GET_BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_budget)],
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu)],
            GET_INGREDIENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ingredients)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    logger.info("Student Meals Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
