import socket
import threading
import re

MessageHandler = 0
NoticeHandler = 1
JoinHandler = 2
LeftHandler = 3
ClearChatHandler = 4
ClearMsgHandler = 5
RoomStateHandler = 6
UserNoticeHandler = 7
UserStateHandler = 8

class bot:

    handlers = []

    def __init__(self, nick, token, server="irc.chat.twitch.tv:6667", prefix=["!"]):
        self.nick = nick
        self.token = token
        self.server = server
        self.prefix = prefix

    def send_packet(self, packet):
        self.sock.send(f"{' '.join(packet)}\n".encode())

    def read_packet(self):
        result = ""
        while True:
            o = self.sock.recv(1)
            if o != b"\n":
                try:
                    result += o.decode()
                except:
                    pass
            else:
                break
        result =  result[:-1].split(" ")
        tags = {}
        new_result = []
        for res in result:
            if res[0] == "@":
                ntags = res[1:].split(";")
                for tag in ntags:
                    tag = tag.split("=")
                    tags[tag[0]] = tag[1]
            else:
                new_result.append(res)
        return new_result, tags

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.server.split(":")[0], int(self.server.split(":")[1])))
        self.send_packet(["PASS", self.token])
        self.send_packet(["NICK", self.nick])
        packet, _ = self.read_packet()
        if len(packet) > 2:
            if packet[1] == "NOTICE":
                response = " ".join(packet[3:])[1:]
                raise ConnectionRefusedError(response)
            else:
                for _ in range(6):
                    self.read_packet()
                self.send_packet(["CAP", "REQ", ":twitch.tv/membership"])
                self.send_packet(["CAP", "REQ", ":twitch.tv/commands"])
                self.send_packet(["CAP", "REQ", ":twitch.tv/tags"])
                self.worker = self.start_handling()
        else:
            raise ConnectionError("Invalid response from server.")

    def disconnect(self):
        self.sock.close()

    def join(self, target):
        self.send_packet(["JOIN", f"#{target.lower()}"])

    def left(self, target):
        self.send_packet(["PART", f"#{target.lower()}"])

    def send_message(self, channel, text):
        self.send_packet(["PRIVMSG", f"#{channel.lower()}", f":{text}"])

    def ban(self, channel, user):
        self.send_message(channel, f"/ban {user}")

    def unban(self, channel, user):
        self.send_message(channel, f"/unban {user}")

    def clear(self, channel):
        self.send_message(channel, "/clear")

    def color(self, channel, color):
        self.send_message(channel, f"/color {color}")

    def delete(self, channel, id):
        self.send_message(channel, f"/delete {id}")

    def me(self, channel, text):
        self.send_message(channel, f"/me {text}")

    def mod(self, channel, user):
        self.send_message(channel, f"/mod {user}")

    def unmod(self, channel, user):
        self.send_message(channel, f"/unmod {user}")

    def add_handler(self, htype, func, filters=[]):
        self.handlers.append([htype, func, filters])

    def on_message(self, *filters):
        def add_handler(func):
            self.add_handler(MessageHandler, func, filters)
            return None
        return add_handler

    def on_notice(self, *filters):
        def add_handler(func):
            self.add_handler(NoticeHandler, func, filters)
            return None
        return add_handler

    def on_join(self, *filters):
        def add_handler(func):
            self.add_handler(JoinHandler, func, filters)
            return None
        return add_handler

    def on_left(self, *filters):
        def add_handler(func):
            self.add_handler(LeftHandler, func, filters)
            return None
        return add_handler

    def on_clearchat(self, *filters):
        def add_handler(func):
            self.add_handler(ClearChatHandler, func, filters)
            return None
        return add_handler

    def on_clearmsg(self, *filters):
        def add_handler(func):
            self.add_handler(ClearMsgHandler, func, filters)
            return None
        return add_handler

    def on_roomstate(self, *filters):
        def add_handler(func):
            self.add_handler(RoomStateHandler, func, filters)
            return None
        return add_handler

    def on_userstate(self, *filters):
        def add_handler(func):
            self.add_handler(UserStateHandler, func, filters)
            return None
        return add_handler

    def on_usernotice(self, *filters):
        def add_handler(func):
            self.add_handler(UserNoticeHandler, func, filters)
            return None
        return add_handler

    def start_handling(self):
        def packet_handler(bot):
            while True:
                packet, tags = bot.read_packet()
                print(packet)
                print(tags)
                
                if len(packet) > 3:
                    if packet[1] == "PRIVMSG":
                        for handler in bot.handlers:
                            if handler[0] == 0:
                                msg = message(packet[2][1:], packet[0].split("!")[0][1:], " ".join(packet[3:])[1:], bot, tags)
                                run = True
                                for fil in handler[2]:
                                    if not fil(msg):
                                        run = False
                                if run:
                                    handler[1](bot, msg)
                    elif packet[1] == "NOTICE":
                        for handler in bot.handlers:
                            if handler[0] == 1:
                                msg = notice(packet[2][1:], " ".join(packet[3:])[1:], bot, tags)
                                run = True
                                for fil in handler[2]:
                                    if not fil(msg):
                                        run = False
                                if run:
                                    handler[1](bot, msg)
                    elif packet[1] == "CLEARMSG":
                        for handler in bot.handlers:
                            if handler[0] == 5:
                                msg = clearmsg(packet[2][1:], " ".join(packet[3:])[1:], bot, tags)
                                run = True
                                for fil in handler[2]:
                                    if not fil(msg):
                                        run = False
                                if run:
                                    handler[1](bot, msg)
                    elif packet[1] == "USERNOTICE":
                        for handler in bot.handlers:
                            if handler[0] == 7:
                                msg = usernotice(packet[2][1:], " ".join(packet[3:])[1:], bot, tags)
                                run = True
                                for fil in handler[2]:
                                    if not fil(msg):
                                        run = False
                                if run:
                                    handler[1](bot, msg)
                elif len(packet) > 2:
                    if packet[1] == "JOIN":
                        for handler in bot.handlers:
                            if handler[0] == 2:
                                msg = join(packet[2][1:], packet[0][1:].split("!")[0], bot, tags)
                                run = True
                                for fil in handler[2]:
                                    if not fil(msg):
                                        run = False
                                if run:
                                    handler[1](bot, msg)
                    elif packet[1] == "PART":
                        for handler in bot.handlers:
                            if handler[0] == 3:
                                msg = left(packet[2][1:], packet[0][1:].split("!")[0], bot, tags)
                                run = True
                                for fil in handler[2]:
                                    if not fil(msg):
                                        run = False
                                if run:
                                    handler[1](bot, msg)
                    elif packet[1] == "CLEARCHAT":
                        for handler in bot.handlers:
                            if handler[0] == 4:
                                if len(packet) == 4:
                                    msg = clearchat(packet[2][1:], packet[3][1:], bot, tags)
                                else:
                                    msg = clearchat(packet[2][1:], None, bot, tags)
                                run = True
                                for fil in handler[2]:
                                    if not fil(msg):
                                        run = False
                                if run:
                                    handler[1](bot, msg)
                    elif packet[1] == "ROOMSTATE":
                        for handler in bot.handlers:
                            if handler[0] == 6:
                                msg = roomstate(packet[2][1:], bot, tags)
                                run = True
                                for fil in handler[2]:
                                    if not fil(msg):
                                        run = False
                                if run:
                                    handler[1](bot, msg)
                    elif packet[1] == "USERSTATE":
                        for handler in bot.handlers:
                            if handler[0] == 8:
                                msg = userstate(packet[2][1:], bot, tags)
                                run = True
                                for fil in handler[2]:
                                    if not fil(msg):
                                        run = False
                                if run:
                                    handler[1](bot, msg)
                elif len(packet) > 1:
                    if packet[0] == "PING":
                        bot.send_packet(["PONG", packet[1]])
        
        worker = threading.Thread(target=packet_handler, args=[self])
        worker.start()
        return worker

    def reconnect(self):
        self.sock.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect()

class message:

    def __init__(self, channel, user, text, bot, tags):
        self.channel = channel
        self.user = user
        self.text = text
        self.bot = bot
        self.tags = tags

    def __getattr__(self, name):
        return self.tags.get(name, None)

    def delete(self):
        self.bot.delete(self.channel, self.id)

    def reply(self, text):
        self.bot.send_message(self.channel, text)
    
    def ban(self):
        self.bot.ban(self.channel, self.user)

    def unban(self):
        self.bot.unban(self.channel, self.user)

    def clear(self):
        self.bot.clear(self.channel)

    def mod(self):
        self.bot.mod(self.channel, self.user)

    def unmod(self):
        self.bot.unmod(self.channel, self.user)

class join:

    def __init__(self, channel, user, bot, tags):
        self.channel = channel
        self.user = user
        self.bot = bot
        self.tags = tags

    def __getattr__(self, name):
        return self.tags.get(name, None)

    def ban(self):
        self.bot.ban(self.channel, self.user)

    def unban(self):
        self.bot.unban(self.channel, self.user)

class left:

    def __init__(self, channel, user, bot, tags):
        self.channel = channel
        self.user = user
        self.bot = bot
        self.tags = tags

    def __getattr__(self, name):
        return self.tags.get(name, None)

    def ban(self):
        self.bot.ban(self.channel, self.user)

    def unban(self):
        self.bot.unban(self.channel, self.user)

class clearchat:

    def __init__(self, channel, user, bot, tags):
        self.channel = channel
        self.user = user
        self.bot = bot
        self.tags = tags

    def __getattr__(self, name):
        return self.tags.get(name, None)

class clearmsg:

    def __init__(self, channel, text, bot, tags):
        self.channel = channel
        self.text = text
        self.bot = bot
        self.tags = tags

    def __getattr__(self, name):
        return self.tags.get(name, None)

class roomstate:

    def __init__(self, channel, bot, tags):
        self.channel = channel
        self.bot = bot
        self.tags = tags

    def __getattr__(self, name):
        return self.tags.get(name, None)

class userstate:

    def __init__(self, channel, bot, tags):
        self.channel = channel
        self.bot = bot
        self.tags = tags

    def __getattr__(self, name):
        return self.tags.get(name, None)

class usernotice:

    def __init__(self, channel, text, bot, tags):
        self.channel = channel
        self.text = text
        self.bot = bot
        self.tags = tags

    def __getattr__(self, name):
        return self.tags.get(name, None)

class notice:
    
    def __init__(self, channel, text, bot, tags):
        self.channel = channel
        self.text = text
        self.bot = bot
        self.tags = tags

    def __getattr__(self, name):
        return self.tags.get(name, None)

class filters:

    def invert(filter):
        return lambda data : not filter(data)

    def text(pattern=None):
        if pattern:
            if isinstance(pattern, re._pattern_type):
                return lambda message : bool(pattern.match(message.text))
            elif type(pattern) == list:
                return lambda message : (message.text in pattern)
            else:
                return lambda message : (message.text == str(pattern))
        else:
            return lambda message : (message.text != "")

    def user(pattern):
        if isinstance(pattern, re._pattern_type):
            return lambda message : bool(pattern.match(message.user))
        elif type(pattern) == list:
            return lambda message : (message.user in pattern)
        else:
            return lambda message : (message.user == str(pattern))

    def channel(pattern):
        if isinstance(pattern, re._pattern_type):
            return lambda message : bool(pattern.match(message.channel))
        elif type(pattern) == list:
            return lambda message : (message.channel in pattern)
        else:
            return lambda message : (message.channel == str(pattern))

    def command(pattern):
        if type(pattern) == list:
            return lambda message : ((message.text[0] in message.bot.prefix) and (message.text[1:] in pattern))
        else:
            return lambda message : ((message.text[0] in message.bot.prefix) and (message.text[1:] == pattern))

    def me():
        return lambda message : (message.user.lower() == message.bot.nick.lower())

    def others():
        return lambda message : (message.user.lower() != message.bot.nick.lower())

    def admin():
        return lambda message : ((message.user.lower() == message.channel) or bool(message.mod))
