# Twithon
![Twithon logo](https://vps.witer33.com/Twithon/TwithonGithub.png)
<p align="center"><b>An easy and fast framework for Twitch chatbot and Twitch API.</b></p>

# A simple bot

``` python
from twithon.bot import bot, MessageHandler, filters, JoinHandler

bot = bot("username", "oauth:token")
bot.connect()

bot.join("channel")

@bot.on_message(filters.command("name"), filters.admin())
def handler(client, message):
    message.reply(message.user)
```
