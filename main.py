import simplematrixbotlib as matrix
import yaml
import pymongo
import requests
from time import time

with open('config.yaml', 'r') as config_file:
    config = yaml.load(config_file, Loader=yaml.BaseLoader)

bot = matrix.Bot(matrix.Creds(config['homeserver'], config['user'], config['pass']))
mongodb = pymongo.MongoClient(config['mongo_uri'])[config['mongo_db']]
print('Connected to MongoDB')
starttime = time()

custom_commands = {}
for command in mongodb['custom-commands'].find():
    custom_commands[command['name']] = command['value']

async def seconds_to_fancytime(seconds, granularity):
    result = []
    intervals = (
        ('days', 86400),
        ('hours', 3600),
        ('minutes', 60),
        ('seconds', 1),
    )

    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append(str(value) + " " + name)
    if len(result) > 1:
        result[-1] = "and " + result[-1]
    if len(result) < 3:
        return ' '.join(result[:granularity])
    else:
        return ', '.join(result[:granularity])

@bot.listener.on_message_event
async def custom_cmds(room, message):
    match = matrix.MessageMatch(room, message, bot, config['prefix'])

    response = ""
    for command in custom_commands:
        if match.command(command):
            response = custom_commands[command]
            break
    if response != "" and match.prefix():
        await bot.api.send_text_message(room.room_id, response)

@bot.listener.on_message_event
async def online_cmds(room, message):
    match = matrix.MessageMatch(room, message, bot, "!")
    if not match.prefix():
        return

    if match.command("uptime"):
        seconds = round(time() - starttime)
        fancytime = await seconds_to_fancytime(seconds, 3)
        await bot.api.send_text_message(room.room_id, f"I have been online for {fancytime}.")
    elif match.command("ping"):
        seconds = requests.get(config['homeserver']).elapsed.total_seconds()
        await bot.api.send_text_message(room.room_id, f"Pong! {round(seconds * 1000)}ms")

bot.run()
