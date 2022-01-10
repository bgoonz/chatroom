"""
Rules:
  No spam
  No offensive messages
  No impersonation
I will delete anything that breaks the rules.

  !refresh
  Refresh the messages. This will remove deleted messages.
  
  !say|stuff
  Say 'stuff' in the chat. This is mostly useless, but
  people who know a password can use it to do spoopy stuff.

  !id|msg
  Get the id of the poster of a message.
  msg is the number to the left of the message.
  This will print the user id.
  
  !run_other|pw|who|command|args
  pw is the password. Only admins know the password. who is who to run
  the command on. It can be in a few formats:
    username - everyone with that username
    !username - everyone except people with that username
    @id - everyone with that user id
    !@id - evryone except people with that user id
    
  command is the command to run. If it was say, it would say something.
  args are the parameters to run the command with.
  
  For example:
    !run_other|password|Clarence|say|hi
    would make every user named Clarence say hi.
    
  !mute|who
  Mute a user. You can't see what they say after this
  But you will have to refresh to remove their previous
  messages. Don't try to hack around this, it's client side.
  
  !unmute|name
  See above.
  
  !exec|code
  Run the code 'code'. Don't try to hack with this, it'll
  only do it to you.
  
  !who
  Shows who is in the room.
  
  !refall|pw
  Password protected (can cause lag). Refreshes everyone.
  
  !change|room
  Move to the room 'room'. You start in 'lobby'.
  
  !room
  Get the current room.
  
  !kick|msg
  Kick YOURSELF.
  
  !color|color|attrs|text
  !c|color|attrs|text
  Say colored text. color is the color.
  attr is the abbreviations for attributes:
    b: bold
    d: dark
    u: underline
    l: blink
    r: reversed
    c: concealed
  So bu would be bold and underlined. Leave attr empty for no attributes.
  text is just what to say.
  
  !pmc|color|attrs|user|text
  Colored pm.
  
  !colordefault|color|attrs
  !cd|color|attrs
  Change your default color. See above for uses.
  
  !announce|pw|text
  !a|pw|text
  Say text in all rooms. Password protected.
  
  !cannounce|color|attrs|pw|text
  !ca|color|attrs|pw|text
  Colored version of announce
  
  !namec|color|attrs
  !nc|color|attrs
  Change your name color. Similar to other color commands. Red is password protected.
"""

import threading
import time
import collections
import itertools
import hashlib
import random
import requests
import re
import atexit # adding a disconnect message, doesnt work right now

# removed 2019
#from termcolor import colored

# new 2019
colors = {
  "grey": "\x1b[30m",
  "red": "\x1b[31m", # the ; lets me have colored name when riutils is dead
  "reed": "\x1b[;31m",
  "green": "\x1b[32m",
  "yellow": "\x1b[33m",
  "blue": "\x1b[34m",
  "magenta": "\x1b[96m",
  "cyan": "\x1b[96m",
  "white": "\x1b[97m",
  "rst": "\x1b[0m",
}
def colored(text, clr,*a, **kw):
	if clr in colors:
		text = colors[clr] + text + colors["rst"]
	return text
print(colored("hi", "red"))
print("the original chat is at https://repl.it/@pyelias/Chatroom-original (broken tho)")
print(colored("go join the repl.it discord server: repl.it/discord", "red"))
input("enter to continue")
# hacks to get screen clear
import sys
import inspect


# end haxz

def clear():
  print("\n" * 100)

import db
from query import *

PW = "a5650dd0d2430ad387b684b34245771bd0d360ecf62ebb6019f81fd06f99b1d9" # hashed password
SEMI_PW = "4420bbe497beac78f1896741d5e10311ee806f1e1eebcb40a50aae9c708e1ef0"

SALT = "pyeliasisawesome" # had to think of a long phrase fast, lol

STAFF = db.ConnectedDatabase("chatroom", "staff").query()
STAFF = [name.lower() for name in STAFF]

SEMI_STAFF = db.ConnectedDatabase("chatroom", "semistaff").query()
SEMI_STAFF = [name.lower() for name in SEMI_STAFF]

PROTECTED = db.ConnectedDatabase("chatroom", "protected").query()
PROTECTED = [name.lower() for name in PROTECTED]

IPW = []

CENSOR_CHAR = "*"

def compile_censored(entry):
  return entry["repl"],re.compile(entry["pattern"],re.IGNORECASE)

def get_censored():
  global CENSORED
  CENSORED = db.ConnectedDatabase("chatroom", "censored").query()
  CENSORED = [compile_censored(entry) for entry in CENSORED]

get_censored()

REAL_CENSORED = CENSORED

CURR_ROOM = None

PUNCTUATION = set("\"',./<>?`1234567890-=+_)(*&^%$#@!~[{]}\|;:")

TIME = [
  ("minute", 60),
  ("hour", 60),
]

ATTR_ABRV = {
  "b": "bold",
  "d": "dark",
  "u": "underline",
  "l": "blink",
  "r": "reversed",
  "c": "concealed",
}

ATTRS = [
  "bold",
  "dark",
  "underline",
  "blink",
  "concealed",
]

COLORS = [
  "grey",
  "red",
  "green",
  "yellow",
  "blue",
  "magenta",
  "cyan",
  "white",
]

SPECIAL_COLORS = [
  "rainbow",
]

RAINBOW_COLORS = [
  "red",
  "green",
  "yellow",
  "blue",
  "magenta",
  "cyan",
]

def sha256(string):
  return hashlib.sha256(bytes(string, "utf-8")).hexdigest()

def md5(string,i=1024,s=""): # actually iterated sha256, too lazy to rename
  res = string
  for _ in range(i):
    res = sha256(res + SALT + s)
  return res
  
def oracle(i,s,o): # some cool crypto stuff
  # new 2019
  return False
  r = requests.post("http://riutils.pythonanywhere.com/",data={'i':i,'s':s,'o':o})
  if r.text not in ["0", "1"]:
    print(r.text)
  return r.text=="1"

def censor(string):
  res = string
  for r, c in REAL_CENSORED:
    res = c.sub(r, res,)
  return res
  
def add_color(text, color, attrs=[]):
  if "reversed" in attrs:
    text = text[::-1]
  attrs_new = [attr for attr in attrs if attr in ATTRS]
  if color == "rainbow":
    res = []
    for char, color in zip(text, itertools.cycle(RAINBOW_COLORS)):
      res.append(colored(char, color, attrs=attrs_new))
    res = "".join(res)
  else:
    res = colored(text, color, attrs=attrs_new)
  
  return res

def does_who_select(who):
  if who == "all":
    return True
  if who[0] == "!":
    return who[1:] not in (name, p_name)
  elif who[0] == "@":
    if who[1] == "!":
      return int(who[2:]) != uid
    else:
      return int(who[1:]) == uid
  else:
    return who in (name, p_name)

class NewMessageGetter():
  def __init__(self, curr_id):
    self.curr_id = curr_id
    self.muted = set()
    self.msgs = []
    self.lmg={'sender':'','text':''}
  
  def fetch_new_messages(self):
    new_messages = messages.query(Attr("id") >= self.curr_id)
    if new_messages:
      self.curr_id = new_messages[-1]["id"] + 1
    return new_messages
  
  def recv_message(self, msg):
    self.msgs.append(msg)
    if "v" in msg and msg["v"] > VERSION:
      print("ERROR: outdated program detected. Try reloading the page, or")
      print("if you are using a forked version, go back to using the")
      print("original program (at repl.it/@replitcode/Pychat) so")
      print("updates can be applied.")
    if 'type' not in msg:
      return
    if 'sender' in msg and 'psender' in msg:
      p_sender = msg["psender"]
      if ("\u001b[31" not in msg['sender']):
        sender = msg['sender']
      elif (
            (
              p_sender.lower() in STAFF or
              p_sender.lower() in SEMI_STAFF
            ) and
            PW in msg.get("ipw", [])
            and
            ("text" not in msg or oracle(1024, str(msg["rid"])+"@"+msg["text"], msg.get("ident","")))
          ):
        sender = msg['sender']
      else:
        sender = 'blatant fake'
    
    if msg["type"] == "announce": # announcements override everything else
      print(f"({msg['id']}) ANNOUNCEMENT: {msg['text']}")
      return
      
    if "room" not in msg or msg["room"] != room_id:
      # if its a different room
      return
    else:
      if CURR_ROOM is not None:
        for pw in CURR_ROOM["pws"]:
          if pw in IPW:
            break
        else:
          return
      
    if "pm_recv" in msg:
      if not does_who_select(msg["pm_recv"]):
        return
      else:
        if "what" in msg and md5(msg["pw"]) == PW:
          COMMANDS[msg["what"]](*msg["args"])
        else:
          print("PM: ", end="")
    
    if msg["type"] == "text": # if its text
      if msg['sender']==self.lmg['sender'] and msg['text']==self.lmg['text']:
        return
      if sender not in self.muted:
        print(f"({str(msg['id']).zfill(5)})  "
              f"{censor(sender)}: {censor(msg['text'])}")
        self.lmg=msg
      if msg['sender'] != name and alive:
        global said_in_a_row
        said_in_a_row = 0
    elif msg["type"] == "command": # if its a command
      ident = str(msg['id']) + msg["command"] + str(msg["args"])
      if does_who_select(msg["who"]) and oracle(1024, ident, msg["pw"]):
        run_command(msg["command"], msg["args"], io=False)
    elif msg["type"] == "who_req":
      if "cmd" in msg:
        if md5(msg["pw"]) == PW and does_who_select(msg["who"]):
          COMMANDS[msg["cmd"]](*msg["args"])
      else:
        pm(sender, "is here.")
  
  def print_new_messages(self):
    for msg in self.fetch_new_messages():
      try:
        self.recv_message(msg)
      except Exception as e:
        print("Unexpected error encountered:")
        print(e)
    sys.stdout.flush()

def refresh(): # refresh the chat
  clear()
  
  curr_msg = messages.curr_id()

  old_message_id = max(curr_msg - 50, 0)
  msg_getter.msgs = []
  msg_getter.curr_id = old_message_id

def say(*what): # say stuff
  global color, attrs
  what = "|".join(what)
  if md5(what) == PW:
    print("nope")
  un_color = what
  what = add_color(what, color, attrs=attrs)
  global room_id
  msg = {
    "type": "text",
    "room": room_id,
    "when": time.time(),
    "sender": name,
    "psender": p_name,
    "ipw": IPW,
    "uid": uid,
    "text": what,
    "ptext": un_color,
    "v": VERSION,
  }
  if pw:
    rid = random.randint(0,1000000)
    ident = str(rid) + "@" + what
    msg["rid"] = rid
    msg["ident"] = md5(pw, 1024, ident)
  global alive
  if alive:
    messages.insert([msg])
  
  global said_in_a_row
  said_in_a_row += 1
  if said_in_a_row >= 10:
    room_id = "spam"

def run_other(*what):
  if what:
    pw, who, command, *args = what
    who = who.replace("@me", f"@{uid}")
    if md5(pw) == PW:
      ident = str(msg_getter.curr_id)+command+str(list(args))
      msg = {
        "type": "command",
        "room": room_id,
        "who": who,
        "pw": md5(pw,1024,ident),
        "command": command,
        "args": list(args),
        "v": VERSION,
      }
      command_pk, = messages.insert([msg])
      time.sleep(1)
      messages.delete(Pks([command_pk]))
    else:
      print("Password incorrect")
  else:
    pw = input("pw: ")
    who = input("who: ")
    command = input("command: ")
    args = input("args: ").split("|")
    run_other(pw, who, command, *args)

def mute(name):
  msg_getter.muted.add(name)

def unmute(name):
  msg_getter.muted.remove(name)

def code_exec(code):
  exec(code.replace(r"\n","\n"), globals(), globals())

def who(*other):
  msg = {
    "type": "who_req",
    "room": room_id,
    "ipw": IPW,
    "sender": name,
    "psender": p_name,
    "v": VERSION,
  }
  pk, = messages.insert([msg])
  time.sleep(1)
  messages.delete(Pks([pk]))

def refall(pw=None):
  if not pw:
    pw = input("pw: ")
  run_other(pw, "all", "refresh")

def fake(pw, who, *what):
  if who in STAFF:
    print("No fake staff.")
    return

  if md5(pw) in (PW, SEMI_PW):
    what = "|".join(what)
    msg = {
      "type": "text",
      "room": room_id,
      "sender": who,
      "ipw": [],
      "psender": who,
      "uid": random.randint(0, 999999),
      "text": what,
      "v": VERSION,
    }
    messages.insert([msg])

def pm(who, *what):
  what = "|".join(what)
  what = add_color(what, color, attrs=attrs)
  msg = {
    "type": "text",
    "when": time.time(),
    "pm_recv": who,
    "ipw": IPW,
    "room": room_id,
    "sender": name,
    "psender": p_name,
    "uid": uid,
    "text": what,
    "v": VERSION,
  }
  if pw:
    rid = random.randint(0,1000000)
    ident = str(rid) + "@" + what
    msg["rid"] = rid
    msg["ident"] = md5(pw, 1024, ident)
  messages.insert([msg])

def when(id_):
  msg = messages.query(Attr("id") == int(id_))
  if msg:
    msg = msg[0]
    if "when" in msg:
      diff = time.time() - msg['when']
      unit = "second"
      for new_unit, scale in TIME:
        if diff >= scale:
          diff /= scale
          unit = new_unit
        else:
          break
      print(f"{round(diff,2)} {unit}s ago.")
    else:
      print("When not supported for that message.")

def reset(pw):
  if md5(pw) == PW:
    messages.clear()
    refall(pw)
  else:
    print("Password incorrect")

def change(room="lobby"):
  private = db.ConnectedDatabase("chatroom","private-rooms").query()
  for priv_room in private:
    if room == priv_room["name"]:
      global CURR_ROOM
      CURR_ROOM = priv_room
      pw = md5(input("Password:"))
      if pw in priv_room["pws"]:
        IPW.append(pw)
        break
      else:
        print("Incorrect password")
        return
      
  global room_id
  room_id = room.lower()
  refresh()

def room():
  if room_id == "spam":
    print("lobby")
  else:
    print(room_id)

def get_id(id_):
  msg = messages.query(Attr("id") == int(id_))
  if msg:
    msg = msg[0]
    if "uid" in msg:
      print(msg["uid"])
    else:
      print("No id")

def kick(msg):
  say(f"was kicked for {msg}")
  global alive
  alive = False
  raise SystemExit(msg)

def color(color, attrs, *what):
  what = "|".join(what)
  attrs = [ATTR_ABRV[attr] for attr in attrs if attr in ATTR_ABRV]
  what = add_color(what, color, attrs=attrs)
  say(what)

def pm_color(color, attrs, user, *what):
  what = "|".join(what)
  what = add_color(what, color, attrs=attrs)
  pm(user, what)

def color_def(color_, attrs_):
  global color, attrs
  if color_ in COLORS or color_ in SPECIAL_COLORS:
    color = color_
    attrs = [ATTR_ABRV[attr] for attr in attrs_ if attr in ATTR_ABRV]
  else:
    print(f"No color {color_}")

def last_ro(dis, pw, who, what, *args):
  msg = {
    "type": "text",
    "when": time.time(),
    "pm_recv": who,
    "room": room_id,
    "sender": name,
    "psender": p_name,
    "ipw": IPW,
    "uid": uid,
    "text": dis,
    "v": VERSION,
    "what": what,
    "args": list(args),
    "pw": pw,
  }
  messages.insert([msg])

def last_ro2(pw, who, what, *args):
  msg = {
    "type": "who_req",
    "room": room_id,
    "sender": name,
    "psender": p_name,
    "v": VERSION,
    "pw": pw,
    "who": who,
    "cmd": what,
    "ipw": IPW,
    "args": list(args),
  }
  pk, = messages.insert([msg])
  time.sleep(1)
  messages.delete(Pks([pk]))

def toggle_censor():
  global REAL_CENSORED
  if REAL_CENSORED:
    REAL_CENSORED = []
    refresh()
    print("Censoring off")
  else:
    REAL_CENSORED = CENSORED
    refresh()
    print("Censoring on")

def announce(pw, *text):
  if md5(pw) == PW:
    msg = {
      "type": "announce",
      "text": "|".join(text),
      "uid": uid,
      "v": VERSION,
    }
    messages.insert([msg])

def c_announce(color, attrs, pw, *text):
  text = "|".join(text)
  attrs = [ATTR_ABRV[attr] for attr in attrs if attr in ATTR_ABRV]
  text = add_color(text, color, attrs=attrs)
  announce(pw, text)

def name_color(color, attrs):
  if color == "red":
    pw = input("Enter password for red: ")
    if md5(pw) != PW:
      print("incorrect")
      return
    else:
      IPW.append(pw)
  attrs = [ATTR_ABRV[attr] for attr in attrs if attr in ATTR_ABRV]
  global name
  name = add_color(p_name, color, attrs=attrs)

def name_change(new_name):
  global name, p_name
  name = p_name = new_name

def update_backend(new_code):
  open("main.py","w").write(new_code)
  print("updates have successfully been installed")

def update_all(pw):
  text = open("main.py").read()
  run_other(pw, "all", "update-backend", text)

COMMANDS = {
  "refresh": refresh,
  "say": say,
  "run_other": run_other,
  "mute": mute,
  "unmute": unmute,
  "exec": code_exec,
  "who": who,
  "refall": refall,
  "fake": fake,
  "pm": pm,
  "when": when,
  "reset": reset,
  "change": change,
  "room": room,
  "id": get_id,
  "kick": kick,
  "color": color,
  "c": color,
  "pmc": pm_color,
  "colordefault": color_def,
  "cd": color_def,
  "lr-ro": last_ro,
  "lr-ro2": last_ro2,
  "toggle-censor": toggle_censor,
  "tc": toggle_censor,
  "announce": announce,
  "a": announce,
  "cannounce": c_announce,
  "ca": c_announce,
  "namec": name_color,
  "nc": name_color,
  "flush": sys.stdout.flush,
  "refc": get_censored,
  "update-backend": update_backend,
  "update-all": update_all,#3###
}

def run_command(command, args, io=True): # run a command
  if io:
    print_ = print
  else:
    print_ = lambda *a, **k: None
  if command in COMMANDS:
    try:
      COMMANDS[command](*args)
      print_("Command complete")
    except Exception as e:
      print(e)
  else:
    print_(f"Command {command} not found")


messages = db.ConnectedDatabase("chatroom", "messages")

VERSION = messages.state

msg_getter = NewMessageGetter(0)

refresh()

def getter_loop():
  while True:
    msg_getter.print_new_messages()
    time.sleep(0.1)

def flush_loop():
  while True:
    sys.stdout.flush()
    time.sleep(1)

banned = db.ConnectedDatabase("chatroom", "banned").query()

name = input("Enter your username: ")[:50]
while "|" in name or "!" in name or "@" in name:
  print("No |, !, or @ in names.")
  name = input("Enter your username: ")[:50]

if name.lower().replace(" ","") in banned:
  print("You are banned")
  raise SystemExit("banned")

pw = None

p_name = name

if name.lower() in STAFF:
  while True:
    pw = input("Enter password for staff account: ")
    if md5(pw) == PW:
      IPW.append(md5(pw))
	  # changed 2019 (oracle ded)
      name = add_color(name, "reed", attrs=["bold"])
      break
    else:
      print("I CHANGED THE PASSWORD")
      print("GO TO THE ADMIN SITE AT https://replitdb.pythonanywhere.com/admin/")
      print("LOG IN AND GO TO GROUPS FOR THE NEW ONE")

elif name.lower() in SEMI_STAFF:
  while True:
    pw = input("Enter password for semi-staff account: ")
    if md5(pw) in [PW, SEMI_PW]:
      IPW.append(md5(pw))
      name = add_color(name, "cyan")
      break
    else:
      print("Password incorrect")
      print("The password was recently changed, if you're an admin")
      print("log in to django and look at Dbs.")

elif name.lower() in PROTECTED:
  while True:
    pw = input("Enter protected password: ")
    if md5(pw) in [PW, SEMI_PW]:
      IPW.append(md5(pw))
      break
    else:
      print("Password incorrect")
      print("The password was recently changed, if you're an admin")
      print("log in to django and look at Dbs.")

if md5(name) == PW:
  print("no password as name")
  exit()

name = name[:50]

clear()

uid = random.randint(0, 999999)

print("Welcome to the chatroom!")
print(__doc__)

input("Press enter to continue")

room_id = "lobby"

alive = True

attrs = []
color = "white"

said_in_a_row = 0

clear()

getter = threading.Thread(target=getter_loop)
getter.daemon = True
getter.start()

time.sleep(1)

say("has joined.")  # user: has joined.

flusher = threading.Thread(target=flush_loop)
flusher.daemon = True
flusher.start()

def leave():
  say("has left.")

atexit.register(leave)

while True:
  msg = input().strip()
  if msg:
    if msg[0] == "!":
      command = msg[1:]
      command, *args = command.split("|") # get command and args
      run_command(command, args) # run it
    else:
      say(msg)
  time.sleep(1)