# 育儿嫂管理 Telegram Bot — 部署指南

## 功能 Features
- 📝 记录育儿嫂事件，自动存档
- 🤖 AI实时分析事件严重程度
- 💬 提供具体的中英文沟通脚本
- 🧠 情绪边界辅导
- 📋 查看历史记录

---

## 第一步：创建 Telegram Bot（2分钟）

1. 打开 Telegram，搜索 **@BotFather**
2. 发送 `/newbot`
3. 按提示取一个名字（如：我的育儿嫂助手）
4. 取一个用户名（必须以 bot 结尾，如：my_nanny_coach_bot）
5. BotFather 会给你一个 **Token**，复制保存好

---

## 第二步：获取 Anthropic API Key

1. 前往 https://console.anthropic.com
2. 注册并创建 API Key
3. 保存好这个 Key

---

## 第三步：部署到 Railway（免费，最简单）

### 方法 A：Railway（推荐，免费额度够用）

1. 前往 https://railway.app，用 GitHub 账号登录
2. 点击 **New Project → Deploy from GitHub repo**
3. 上传这个文件夹到你的 GitHub（或直接用 Railway CLI）
4. 在 Railway 项目的 **Variables** 里添加：
   ```
   TELEGRAM_BOT_TOKEN = 你的Telegram Token
   ANTHROPIC_API_KEY  = 你的Anthropic Key
   ```
5. Railway 会自动检测 `requirements.txt` 并启动

### 方法 B：本地运行（测试用）

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export TELEGRAM_BOT_TOKEN="你的token"
export ANTHROPIC_API_KEY="你的key"

# 运行
python bot.py
```

### 方法 C：Render（免费，但有冷启动）

1. 前往 https://render.com
2. New → Web Service → 连接你的 GitHub repo
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python bot.py`
5. 添加环境变量同上

---

## Bot 命令说明

| 命令 | 功能 |
|------|------|
| `/start` | 主菜单 |
| `/log` | 记录新事件（会自动存档+分析） |
| `/advice` | 获取具体沟通建议 |
| `/history` | 查看近期记录 |
| `/rules` | 查看家规摘要 |
| `/clear` | 清除当前对话记忆 |

或者直接发消息描述情况，Bot 会立即给出建议！

---

## 使用示例

**你发送：**
> 阿姨今天做饭时一直在玩手机，饭烧糊了

**Bot 回复：**
> ⚠️ **严重程度：中等违规**
>
> 你的感受完全合理，这已经是影响到孩子安全的问题了。
>
> **建议立即说：**
> 🇨🇳 "我需要和你说一件事。今天做饭时手机的问题，饭烧糊了，这不是第一次了。工作时间内做饭时请不要用手机，这是安全问题。"
>
> 🇬🇧 "I need to address something. The phone use during cooking today caused the food to burn again. During working hours, especially cooking, please keep your phone away — this is a safety issue."
>
> **边界提醒：** 不要因为怕尴尬而等待。这类问题说得越晚，阿姨越会认为这是可以接受的行为。

---

## 数据存储

事件记录保存在 `incidents.jsonl` 文件中（JSON格式，每行一条记录）。
可以用任何文本编辑器查看，或导入 Excel。
