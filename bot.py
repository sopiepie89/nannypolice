"""
Nanny Management Telegram Bot
Powered by Claude AI - Helps track incidents and gives real-time coaching
"""

import os
import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
import anthropic

# ── Configuration ──────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
LOG_FILE = "incidents.jsonl"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ── System Prompt ───────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a compassionate but firm household management coach helping a mother 
manage her live-in nanny. You have deep knowledge of her household rules (summarised below) 
and her history with previous nannies.

HOUSEHOLD RULES SUMMARY:
1. Accommodation: No renegotiating arrangements after arrival. No co-sleeping without permission.
2. Child Feeding: Follow parental instructions strictly. No unauthorised changes to milk/food amounts.
3. Child Safety: Full attention during care. No phone use during active childcare or cooking.
4. Hygiene: Dispose of waste immediately. No excessive food consumption.
5. Care for mother: Nanny prepares mother's meals on time. No delegating duties to grandparents.
6. Professional conduct: No comments on employer's appearance/lifestyle. No gossip. Maintain distance.
7. Personal belongings: Never touch, borrow, or use employer's personal items. Serious breach.
8. Phone use: Prohibited during working hours (childcare, cooking, outdoor supervision).

EMPLOYER BACKGROUND:
- Has a young child
- Has had traumatic experiences with multiple nannies: co-sleeping violations, unauthorised feeding 
  changes, personal item theft (Goyard bag used without permission), delegation to grandparents, 
  verbal insults about appearance and lifestyle, falling asleep while holding baby, phone addiction
- Feels emotionally exhausted and has lost trust in live-in helpers
- Tends to avoid confrontation and "let things slide" which creates bigger problems later
- Needs help knowing EXACTLY what to say and when

YOUR ROLE:
When the employer logs an incident or asks for advice:
1. Validate their feelings briefly (1-2 sentences max)
2. Classify the severity: Minor / Moderate / Serious / Termination-level
3. Give a CLEAR recommended action with exact script (what to say word-for-word in Chinese and English)
4. Give a boundary-setting reminder if they seem to be minimising the issue
5. If asked about emotional boundaries, help them identify when they are over-accommodating

Keep responses concise, warm but direct. Use clear formatting with emojis for readability.
Always respond in the same language the user writes in (Chinese or English).
If Chinese, respond in Chinese with English scripts for what to say to the nanny."""

# ── Incident Storage ────────────────────────────────────────────────────────────
def log_incident(user_id: int, text: str, category: str = "general"):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "category": category,
        "description": text
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def get_recent_incidents(user_id: int, limit: int = 10) -> list:
    if not os.path.exists(LOG_FILE):
        return []
    incidents = []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get("user_id") == user_id:
                    incidents.append(entry)
            except json.JSONDecodeError:
                continue
    return incidents[-limit:]

# ── Conversation Memory (per session) ──────────────────────────────────────────
user_conversations: dict[int, list] = {}

def get_conversation(user_id: int) -> list:
    return user_conversations.get(user_id, [])

def add_to_conversation(user_id: int, role: str, content: str):
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    user_conversations[user_id].append({"role": role, "content": content})
    # Keep last 20 messages to manage context
    if len(user_conversations[user_id]) > 20:
        user_conversations[user_id] = user_conversations[user_id][-20:]

# ── AI Coaching ─────────────────────────────────────────────────────────────────
def get_ai_response(user_id: int, user_message: str) -> str:
    add_to_conversation(user_id, "user", user_message)
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=get_conversation(user_id)
        )
        assistant_message = response.content[0].text
        add_to_conversation(user_id, "assistant", assistant_message)
        return assistant_message
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return "⚠️ 抱歉，AI助手暂时无法响应，请稍后重试。\n\nSorry, the AI coach is temporarily unavailable. Please try again shortly."

# ── Command Handlers ────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📝 记录新事件 Log Incident", callback_data="log")],
        [InlineKeyboardButton("💬 获取建议 Get Advice", callback_data="advice")],
        [InlineKeyboardButton("📋 查看记录 View Log", callback_data="view_log")],
        [InlineKeyboardButton("🧠 情绪边界 Emotional Boundaries", callback_data="boundaries")],
        [InlineKeyboardButton("🗑️ 清除对话 Clear Chat", callback_data="clear")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome = (
        "👶 *育儿嫂管理助手*\n"
        "_Nanny Management Coach_\n\n"
        "我在这里帮助你记录、管理和处理与育儿嫂相关的情况。\n\n"
        "I'm here to help you log incidents, get coaching on what to say, "
        "and manage your emotional boundaries with your nanny.\n\n"
        "选择一个选项开始，或者直接告诉我发生了什么：\n"
        "_Choose an option below, or just tell me what happened:_"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown", reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 *可用命令 / Commands*\n\n"
        "/start — 主菜单 Main menu\n"
        "/log — 记录事件 Log an incident\n"
        "/advice — 获取建议 Get coaching advice\n"
        "/history — 查看近期记录 View recent logs\n"
        "/clear — 清除对话记忆 Clear conversation\n"
        "/rules — 查看家规摘要 View household rules\n\n"
        "💡 或者直接发消息描述情况，我会立即给出建议！\n"
        "_Or just send a message describing the situation!_"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rules_text = (
        "📋 *家规摘要 / Household Rules Summary*\n\n"
        "1️⃣ *住宿* — 不得要求更改约定安排，禁止未经同意同睡\n"
        "2️⃣ *喂养* — 严格遵照父母指示，禁止擅自调整奶量\n"
        "3️⃣ *安全* — 带娃时全程专注，禁止使用手机\n"
        "4️⃣ *卫生* — 立即处理垃圾，合理使用食材\n"
        "5️⃣ *产妇照顾* — 按时准备餐食，不得推诿给家中老人\n"
        "6️⃣ *职业态度* — 禁止评价雇主外貌/生活，禁止八卦\n"
        "7️⃣ *私人物品* — 严禁触碰或使用雇主任何私人物品\n"
        "8️⃣ *手机* — 工作时间禁止使用手机\n\n"
        "⚖️ *违规等级*：一般提醒 → 正式警告 → 即时终止合同"
    )
    await update.message.reply_text(rules_text, parse_mode="Markdown")

async def log_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 *记录事件 / Log an Incident*\n\n"
        "请描述发生了什么（中文或英文均可）：\n"
        "_Describe what happened (Chinese or English):_",
        parse_mode="Markdown"
    )
    context.user_data["mode"] = "logging"

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    incidents = get_recent_incidents(user_id, limit=8)
    
    if not incidents:
        await update.message.reply_text(
            "📂 还没有记录。\n_No incidents logged yet._"
        )
        return
    
    text = "📋 *近期记录 / Recent Incidents*\n\n"
    for i, inc in enumerate(reversed(incidents), 1):
        dt = datetime.fromisoformat(inc["timestamp"]).strftime("%m/%d %H:%M")
        preview = inc["description"][:80] + ("..." if len(inc["description"]) > 80 else "")
        text += f"*{i}.* `{dt}` — {preview}\n\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_conversations:
        del user_conversations[user_id]
    await update.message.reply_text(
        "🗑️ 对话记忆已清除。\n_Conversation memory cleared. Fresh start!_"
    )

# ── Callback Query Handler ──────────────────────────────────────────────────────
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "log":
        await query.message.reply_text(
            "📝 请描述发生了什么：\n_Describe what happened:_"
        )
        context.user_data["mode"] = "logging"
    
    elif query.data == "advice":
        await query.message.reply_text(
            "💬 请描述你遇到的情况，我来帮你分析并告诉你该说什么：\n"
            "_Describe the situation and I'll tell you exactly what to say:_"
        )
        context.user_data["mode"] = "advice"
    
    elif query.data == "view_log":
        await history_command(update, context)
    
    elif query.data == "boundaries":
        user_id = update.effective_user.id
        response = get_ai_response(
            user_id,
            "请给我一些关于如何与育儿嫂保持情绪边界的建议，特别是在我有迁就她的倾向时应该如何识别和处理。"
        )
        await query.message.reply_text(response, parse_mode="Markdown")
    
    elif query.data == "clear":
        user_id = update.effective_user.id
        if user_id in user_conversations:
            del user_conversations[user_id]
        await query.message.reply_text("🗑️ 对话已清除！ _Cleared!_")

# ── Main Message Handler ────────────────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    mode = context.user_data.get("mode", "chat")
    
    # Show typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )
    
    # Log incident if in logging mode
    if mode == "logging":
        log_incident(user_id, user_text)
        prompt = f"我刚刚记录了一个新事件：{user_text}\n\n请帮我分析这个情况的严重性，并告诉我应该如何处理，包括具体该说的话。"
        context.user_data["mode"] = "chat"
    else:
        prompt = user_text
    
    # Get AI response
    response = get_ai_response(user_id, prompt)
    
    # Send response (split if too long for Telegram's 4096 char limit)
    if len(response) > 4000:
        parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
        for part in parts:
            await update.message.reply_text(part, parse_mode="Markdown")
    else:
        try:
            await update.message.reply_text(response, parse_mode="Markdown")
        except Exception:
            # Fallback without markdown if parsing fails
            await update.message.reply_text(response)

# ── Main ────────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("log", log_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CommandHandler("rules", rules_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("🤖 Nanny Management Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
