# Twithon
<p align="center"><img width="750px" src="https://vps.witer33.com/Twithon/TwithonGithub.png?lol"></p>
<p align="center"><b>A python wrapper over Twitch API to build bots and applications.</b></p>
<p align="center"><i>Documentation: COMING SOON</i></p>

# A simple bot

``` python
from twithon.bot import bot, filters

bot = bot("username", "oauth:token", channels=["channel"])
bot.connect()

@bot.on_message(filters.command("name"), filters.admin())
def handler(client, message):
    message.reply(message.user)
```
