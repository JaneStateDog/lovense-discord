import discord
from buttplug import Client, WebsocketConnector, ProtocolSpec

import asyncio
import json
import os

d_client = discord.Client()

b_client = Client("Discord Client", ProtocolSpec.v3)
connector = WebsocketConnector("ws://127.0.0.1:12345", logger = b_client.logger)
device = 0

is_open = True

print("Loading file")
data = {}
if os.path.isfile("data.json"):
    with open("data.json", "r") as file:
        data = json.load(file)
else:
    with open("data.json", "x") as file:
        pass

options = {}
if os.path.isfile("options.json"):
    with open("options.json", "r") as file:
        options = json.load(file)
else:
    with open("options.json", "x") as file:
        json.dump({ "key": "" }, file, ensure_ascii = False, indent = 4)

queue_butt = []
queue_higher = []

async def connect_toy():
    global device

    # Connect to the server
    await b_client.connect(connector)
    
    # Scan until we find a device
    await b_client.start_scanning()
    while len(b_client.devices) == 0:
        print("Waiting for device...")
        await asyncio.sleep(1)

    await b_client.stop_scanning()

    print("Found device! Sending test vibration (brace yourself)")
    device = b_client.devices[0]
    await vibrate(device, 0, 1, 0.2)

async def vibrate(device, actuator, power, duration):
    if device == 0:
        return

    await device.actuators[actuator].command(power / 10)
    await asyncio.sleep(duration)
    await device.actuators[actuator].command(0)

@d_client.event
async def on_ready():
    print("Logged in as " + str(d_client.user) + "")

@d_client.event
async def on_message(message):
    global is_open

    args = message.content.split(" ")
    if args[0] == ">vibe" and is_open:
        try:
            power = float(args[1])
            duration = float(args[2])
            if len(args) == 4:
                actuator = int(args[3]) # The acutator is not talked about in the bio and is optional
            else:
                actuator = 0
        except:
            print("That is not a valid command")
            return

        print("Received command from " + str(message.author) + " to vibe actuator " + str(actuator) + " for " + str(duration) + " seconds at power level " + str(power))
        author = str(message.author)
        if author in data:
            data[author] += 1
        else:
            data[author] = 1

        #if actuator == 0:
            #queue_butt.append((power, duration))
        #elif actuator == 1:
            #queue_higher.append((power, duration))

        await vibrate(device, 0, power, duration)

        #await message.channel.send("Ahhnn~ :flushed:")
    elif args[0] == ">open" and not is_open and message.author == d_client.user:
        print("Changing bio to opening")
        #await d_client.user.edit(bio = ':heart: Fun is online\n||`>vibe (power 1-10) (duration in seconds)` :wink:||')

        print("Ready!")

        is_open = True

    elif args[0] == ">close" and is_open and message.author == d_client.user:
        is_open = False

        print("Disconnecting toy")
        await b_client.disconnect()

        print("Changing bio to closing")
        #await d_client.user.edit(bio = ":broken_heart: Fun is offline")

        print("Disconnecting from Discord")
        await d_client.close()

async def main():
    await connect_toy()
    await d_client.start(options["key"])

asyncio.run(main())

print("Saving file")
with open("data.json", "w") as file:
    json.dump(data, file, ensure_ascii = False, indent = 4)