from telegram import Bot
import config

bot = Bot(token=config.TOKEN)
bot.get_updates(offset=-1)  # сброс всех pending updates
print("Очередь getUpdates очищена")
