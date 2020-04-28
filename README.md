# Twithon
<p align="center"><img width="750px" src="https://vps.witer33.com/Twithon/TwithonGithub.png?updated"></p>
<p align="center"><b>A python wrapper over Twitch API to build bots and applications.</b></p>
<p align="center"><i>Documentation: COMING SOON</i></p>

# A simple bot

``` python
from twithon.bot import Bot, Filters

bot = Bot("username", "oauth:token", channels=["channel"])
bot.connect()

@bot.on_message(Filters.command("name"), Filters.admin())
def handler(client, message):
    message.reply(message.user)
```

# Installation

```
pip3 install twithon
```
