import asyncio
import json
import logging
import websockets
import random
from collections import OrderedDict

logging.basicConfig()

USERPOSE = []

USERS = OrderedDict()
WINERS = []
LOSERS = []

async def win():
    winers = set()
    agents = set()
    killers = set()
    users = list(USERS.values())
    for user in users:
        if user["role"] == "agent":
            USERPOSE[user["shoot"]]["alive"] = False
            if users[user["shoot"]]["role"] == "taunt" or users[user["shoot"]]["role"] == "red taunt":
                winers.add(users[user["shoot"]]["index"])
    for user in users:
        if user["role"] == "killer" and USERPOSE[user["index"]]["alive"]:
            USERPOSE[user["shoot"]]["alive"] = False
            if users[user["shoot"]]["role"] == "taunt" or users[user["shoot"]]["role"] == "blue taunt":
                winers.add(users[user["shoot"]]["index"])
    boss = 0
    for user in users:
        if user["role"] == "boss":
          boss = user["index"]
        if user["role"] == "npc" and USERPOSE[user["index"]]["alive"]:
            winers.add(user["index"])
        if user["role"] == "boss" or user["role"] == "agent" or user["role"] == "blue taunt":
            agents.add(user["index"])
        if user["role"] == "killer" or user["role"] == "red taunt" :
            killers.add(user["index"])
    if  USERPOSE[boss]["alive"]:
        winers.update(agents)
        print("blue")
    else:
        print("red")
        winers.update(killers)
    losers = set(range(len(users))) 
    losers.difference_update(winers)
    for loser in losers:
        LOSERS.append([loser, USERPOSE[loser]["name"]])
    for winer in winers:
        WINERS.append([winer, USERPOSE[winer]["name"]])
    await notify_all()    


async def on_admin(data, websocket):
    if data["cm"] == "start":
        print("start")
        give_cards(data["num"])
        await notify_all()
    if data["cm"] == "shuffle":
        print("shuffle " + str(data["num"]))
        await shuffle(data["num"])
    if data["cm"] == "shift":
        print("shift")
        await shift()
    if data["cm"] == "win":
        print("win")
        await win()
    if data["cm"] == "dsc":
        print("dsc")
        await unregister(websocket)
    if data["cm"] == "reset":
        print("restart")
        await reset()
        print(LOSERS) 
        print(WINERS)
        print(USERPOSE)
        print(USERS)       

async def reset():
    global WINERS
    global LOSERS
    for key in USERS:
        USERS[key]["role"] = None
        USERS[key]["shoot"] = 0
    for user in USERPOSE:
        user["alive"] = True
        user["role"] = "🌰"
    WINERS = []
    LOSERS = []
    await notify_all()
async def shift():
    print("shift")
    users = list(USERS.values())
    tmp = users[0]["role"]
    for x in range(1, len(USERS)):
        tmp, users[x]["role"] = users[x]["role"], tmp
    users[0]["role"] = tmp
    z = 0
    for x in USERS:
        USERS[x]=users[z]
        z+=1

    await notify_all()

async def shuffle(id):
    l = list(USERS.values())
    k = list(USERS.keys())
    roles = [l[id-1]["role"], l[id]["role"], l[id+1]["role"]]
    random.shuffle(roles)
    USERS[k[id-1]]["role"], USERS[k[id]]["role"], USERS[k[id+1]]["role"] = roles[0], roles[1], roles[2]
    #for user in list(USERS.keys())[id-2:id+1]:
    #   await notify(user)
    await notify_all()

def give_cards(n):
    if n == 5:
        roles = ["boss", "agent", "killer", "red taunt", "npc"]
    elif n == 6:
        roles = ["boss", "agent", "killer", "blue taunt", "killer", "npc"]
    else:
        print("jopa with players")
    random.shuffle(roles)
    usersObj = list(USERS.values())
    for x in range(n):
        usersObj[x]["role"] = roles[x]

async def on_message(data, websocket):
    index = USERS[websocket]["index"]
    if data["cm"] == "give":
        print("start")
        give_cards(5)
        await notify_all()
    elif data["cm"] == "chname":
        USERPOSE[index]["name"] = data["name"]
        await notify_all()
    elif data["cm"] == "chrole":
        USERPOSE[index]["role"] = data["role"]
        await notify_all()
    elif data["cm"] == "chshoot":
        USERS[websocket]["shoot"] = data["index"]


async def notify_all():
    if USERS:  # asyncio.wait doesn't accept an empty list
        for user in USERS:
            await notify(user)


async def notify(user):
            userState = {"cm": "state", "users": USERPOSE, "state": USERS[user], "winers": WINERS, "losers":LOSERS}
            await user.send(json.dumps(userState))

async def register(websocket):
    print("new user")
    USERPOSE.append({"name": "vasya", "role": "🌰", "alive": True})
    USERS[websocket] = { "role": None, "index": len(USERPOSE) - 1, "shoot": 0 }
    await notify_all()


async def unregister(websocket):
    USERPOSE.pop(USERS[websocket]["index"])
    USERS.pop(websocket)
    await notify_all()

async def counter(websocket, path):
    # register(websocket) sends user_event() to websocket

    try:
        await register(websocket)
        async for message in websocket:
            data = json.loads(message)
            print(data)
            if  "admin" not in message:
                await on_message(data, websocket)
            else:
             await   on_admin(data, websocket)
    finally:
        await unregister(websocket)

port = 6765
start_server = websockets.serve(counter, "localhost", port)
print("running on "+str(port))
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()