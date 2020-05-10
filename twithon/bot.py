import socket
import threading
import re
import time
import queue

MessageHandler = 0
NoticeHandler = 1
JoinHandler = 2
LeftHandler = 3
ClearChatHandler = 4
ClearMsgHandler = 5
RoomStateHandler = 6
UserNoticeHandler = 7
UserStateHandler = 8

class Bot:

    handlers = []
    stop = False

    def __init__(self, nick, token, server="irc.chat.twitch.tv:6667", prefix=["!"], channels=[], workers=5):
        self.nick = nick
        self.token = token
        self.server = server
        self.prefix = prefix
        self.channels = channels
        self.workers = workers
        self.exes = queue.Queue()
        self.packet_lock = threading.Lock()

    def send_packet(self, packet):
        """
        Send an array of string as a simple packet.
        """
        with self.packet_lock:
            self.sock.send("{}\n".format(' '.join(packet)).encode())

    def read_packet(self):
        """
        Read a packet and parse its tags.
        """
        result = ""
        while True:
            try:
                o = self.sock.recv(1)
            except:
                return None, None
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
        """
        Make a connection to the Twitch IRC server and login.
        """
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
                for channel in self.channels:
                    self.send_packet(["JOIN", "#{}".format(channel.lower())])
                self.worker = self.start_handling()
        else:
            raise ConnectionError("Invalid response from server.")

    def disconnect(self):
        self.stop = True
        self.sock.close()

    def join(self, target):
        self.channels.append(target)
        self.send_packet(["JOIN", "#{}".format(target.lower())])

    def left(self, target):
        try:
            self.channels.remove(target)
        except:
            pass
        self.send_packet(["PART", "#{}".format(target.lower())])

    def send_message(self, channel, text):
        self.send_packet(["PRIVMSG", "#{}".format(channel.lower()), ":{}".format(text)])

    def ban(self, channel, user):
        self.send_message(channel, "/ban {}".format(user))

    def unban(self, channel, user):
        self.send_message(channel, "/unban {}".format(user))

    def clear(self, channel):
        self.send_message(channel, "/clear")

    def color(self, channel, color):
        self.send_message(channel, "/color {}".format(color))

    def delete(self, channel, id):
        self.send_message(channel, "/delete {}".format(id))

    def me(self, channel, text):
        self.send_message(channel, "/me {}".format(text))

    def mod(self, channel, user):
        self.send_message(channel, "/mod {}".format(user))

    def unmod(self, channel, user):
        self.send_message(channel, "/unmod {}".format(user))

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
        """
        Start handling packets.
        """
        def packet_handler(bot):
            while True:
                packet, tags = bot.read_packet()
                if not packet:
                    bot.stop = True
                    time.sleep(0.2)
                    bot.stop = False
                    return

                if len(packet) > 3:
                    if packet[1] == "PRIVMSG":
                        for handler in bot.handlers:
                            if handler[0] == 0:
                                msg = Message(packet[2][1:], packet[0].split("!")[0][1:], " ".join(packet[3:])[1:], bot, tags)
                                run = True
                                for fil in handler[2]:
                                    if not fil(msg):
                                        run = False
                                if run:
                                    self.exes.put([handler[1], [bot, msg]])
                    elif packet[1] == "NOTICE":
                        for handler in bot.handlers:
                            if handler[0] == 1:
                                msg = Notice(packet[2][1:], " ".join(packet[3:])[1:], bot, tags)
                                run = True
                                for fil in handler[2]:
                                    if not fil(msg):
                                        run = False
                                if run:
                                    self.exes.put([handler[1], [bot, msg]])
                    elif packet[1] == "CLEARMSG":
                        for handler in bot.handlers:
                            if handler[0] == 5:
                                msg = Clearmsg(packet[2][1:], " ".join(packet[3:])[1:], bot, tags)
                                run = True
                                for fil in handler[2]:
                                    if not fil(msg):
                                        run = False
                                if run:
                                    self.exes.put([handler[1], [bot, msg]])
                    elif packet[1] == "USERNOTICE":
                        for handler in bot.handlers:
                            if handler[0] == 7:
                                msg = Usernotice(packet[2][1:], " ".join(packet[3:])[1:], bot, tags)
                                run = True
                                for fil in handler[2]:
                                    if not fil(msg):
                                        run = False
                                if run:
                                    self.exes.put([handler[1], [bot, msg]])
                elif len(packet) > 2:
                    if packet[1] == "JOIN":
                        for handler in bot.handlers:
                            if handler[0] == 2:
                                msg = Join(packet[2][1:], packet[0][1:].split("!")[0], bot, tags)
                                run = True
                                for fil in handler[2]:
                                    if not fil(msg):
                                        run = False
                                if run:
                                    self.exes.put([handler[1], [bot, msg]])
                    elif packet[1] == "PART":
                        for handler in bot.handlers:
                            if handler[0] == 3:
                                msg = Left(packet[2][1:], packet[0][1:].split("!")[0], bot, tags)
                                run = True
                                for fil in handler[2]:
                                    if not fil(msg):
                                        run = False
                                if run:
                                    self.exes.put([handler[1], [bot, msg]])
                    elif packet[1] == "CLEARCHAT":
                        for handler in bot.handlers:
                            if handler[0] == 4:
                                if len(packet) == 4:
                                    msg = Clearchat(packet[2][1:], packet[3][1:], bot, tags)
                                else:
                                    msg = Clearchat(packet[2][1:], None, bot, tags)
                                run = True
                                for fil in handler[2]:
                                    if not fil(msg):
                                        run = False
                                if run:
                                    self.exes.put([handler[1], [bot, msg]])
                    elif packet[1] == "ROOMSTATE":
                        for handler in bot.handlers:
                            if handler[0] == 6:
                                msg = Roomstate(packet[2][1:], bot, tags)
                                run = True
                                for fil in handler[2]:
                                    if not fil(msg):
                                        run = False
                                if run:
                                    self.exes.put([handler[1], [bot, msg]])
                    elif packet[1] == "USERSTATE":
                        for handler in bot.handlers:
                            if handler[0] == 8:
                                msg = Userstate(packet[2][1:], bot, tags)
                                run = True
                                for fil in handler[2]:
                                    if not fil(msg):
                                        run = False
                                if run:
                                    self.exes.put([handler[1], [bot, msg]])
                elif len(packet) > 1:
                    if packet[0] == "PING":
                        bot.send_packet(["PONG", packet[1]])
                    elif packet[0] == "RECONNECT":
                        for channel in self.channels:
                            self.join(channel)
                elif len(packet) == 1:
                    if packet[0] == "RECONNECT":
                        for channel in self.channels:
                            self.join(channel)        
        
        def exes_worker(bot):
            while True:
                if bot.stop:
                    return
                try:
                    func = bot.exes.get(timeout=0.1)
                except queue.Empty:
                    continue
                bot.exes.task_done()
                func[0](*func[1])

        for _ in range(self.workers):
            worker = threading.Thread(target=exes_worker, args=[self])
            worker.start()
        worker = threading.Thread(target=packet_handler, args=[self])
        worker.start()
        return worker

    def reconnect(self):
        self.disconnect()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect()

class Module(Bot):

    def __init__(self, bot):
        self.bot = bot
        self.enabled = True
        self.handlers()

    def enable_check(self):
        return (lambda message : self.enabled)

    def disable(self):
        self.enabled = False

    def enable(self):
        self.enabled = True

    def on_message(self, *filters):
        filters = list(filters)
        filters.append(self.enable_check())
        def add_handler(func):
            self.bot.add_handler(MessageHandler, func, filters)
            return None
        return add_handler

    def on_notice(self, *filters):
        filters = list(filters)
        filters.append(self.enable_check())
        def add_handler(func):
            self.bot.add_handler(NoticeHandler, func, filters)
            return None
        return add_handler

    def on_join(self, *filters):
        filters = list(filters)
        filters.append(self.enable_check())
        def add_handler(func):
            self.bot.add_handler(JoinHandler, func, filters)
            return None
        return add_handler

    def on_left(self, *filters):
        filters = list(filters)
        filters.append(self.enable_check())
        def add_handler(func):
            self.bot.add_handler(LeftHandler, func, filters)
            return None
        return add_handler

    def on_clearchat(self, *filters):
        filters = list(filters)
        filters.append(self.enable_check())
        def add_handler(func):
            self.bot.add_handler(ClearChatHandler, func, filters)
            return None
        return add_handler

    def on_clearmsg(self, *filters):
        filters = list(filters)
        filters.append(self.enable_check())
        def add_handler(func):
            self.bot.add_handler(ClearMsgHandler, func, filters)
            return None
        return add_handler

    def on_roomstate(self, *filters):
        filters = list(filters)
        filters.append(self.enable_check())
        def add_handler(func):
            self.bot.add_handler(RoomStateHandler, func, filters)
            return None
        return add_handler

    def on_userstate(self, *filters):
        filters = list(filters)
        filters.append(self.enable_check())
        def add_handler(func):
            self.bot.add_handler(UserStateHandler, func, filters)
            return None
        return add_handler

    def on_usernotice(self, *filters):
        filters = list(filters)
        filters.append(self.enable_check())
        def add_handler(func):
            self.bot.add_handler(UserNoticeHandler, func, filters)
            return None
        return add_handler

class Message:

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

class Join:

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

class Left:

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

class Clearchat:

    def __init__(self, channel, user, bot, tags):
        self.channel = channel
        self.user = user
        self.bot = bot
        self.tags = tags

    def __getattr__(self, name):
        return self.tags.get(name, None)

class Clearmsg:

    def __init__(self, channel, text, bot, tags):
        self.channel = channel
        self.text = text
        self.bot = bot
        self.tags = tags

    def __getattr__(self, name):
        return self.tags.get(name, None)

class Roomstate:

    def __init__(self, channel, bot, tags):
        self.channel = channel
        self.bot = bot
        self.tags = tags

    def __getattr__(self, name):
        return self.tags.get(name, None)

class Userstate:

    def __init__(self, channel, bot, tags):
        self.channel = channel
        self.bot = bot
        self.tags = tags

    def __getattr__(self, name):
        return self.tags.get(name, None)

class Usernotice:

    def __init__(self, channel, text, bot, tags):
        self.channel = channel
        self.text = text
        self.bot = bot
        self.tags = tags

    def __getattr__(self, name):
        return self.tags.get(name, None)

class Notice:
    
    def __init__(self, channel, text, bot, tags):
        self.channel = channel
        self.text = text
        self.bot = bot
        self.tags = tags

    def __getattr__(self, name):
        return self.tags.get(name, None)

class Filters:

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

    def lower_text(pattern):
        if type(pattern) == list:
            return lambda message : (message.text.lower() in pattern)
        else:
            return lambda message : (message.text.lower() == str(pattern).lower())

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
        return lambda message : ((message.user.lower() == message.channel) or bool(int(message.tags["mod"])))
