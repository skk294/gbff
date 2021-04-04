import sys
import json
import asyncio
import websockets
import raidboss_pb2
import raidtweet_pb2


async def get_allraidboss():
    headers = websockets.http.Headers()
    headers["Sec-WebSocket-Protocol"] = "binary"
    headers["User-Agent"] = "User-Agent,Mozilla/5.0 (Windows NT 6.1; rv,2.0.1) Gecko/20100101 Firefox/4.0.1"
    uri = "wss://gbf-raidfinder-tw.herokuapp.com/ws/raids?keepAlive=true"
    raidbossesresponse = raidboss_pb2.RaidBossesResponse()
    allraidboss_list = []
    async with websockets.connect(uri, subprotocols="binary", extra_headers=headers) as websocket:
        while True:
            _recv = await websocket.recv()
            if b"SNAPSHOT" in _recv:
                await websocket.send(b"\x0a\x00")
            if len(_recv) > 10000:
                raidbossesresponse.ParseFromString(_recv[4:])
                for raidboss, index in zip(
                    raidbossesresponse.raidBosses,
                    range(len(raidbossesresponse.raidBosses)),
                ):
                    raidboss_dict = {}
                    for field, value in raidboss.ListFields():
                        raidboss_dict[field.name] = value
                    raidboss_dict["index"] = index
                    allraidboss_list.append(raidboss_dict)
                break
    if allraidboss_list:
        with open("allraidboss.json", "w") as f:
            f.write(json.dumps({"allraidboss": allraidboss_list}))
        print("完成.")
    else:
        print("failed.")


async def subscribe_boss(*args):
    allraidboss_list = []
    with open("allraidboss.json", "r", encoding="utf-8") as f:
        allraidboss_list = json.loads(f.read())["allraidboss"]
    headers = websockets.http.Headers()
    headers["Sec-WebSocket-Protocol"] = "binary"
    headers["User-Agent"] = "User-Agent,Mozilla/5.0 (Windows NT 6.1; rv,2.0.1) Gecko/20100101 Firefox/4.0.1"
    uri = "wss://gbf-raidfinder-tw.herokuapp.com/ws/raids?keepAlive=true"
    raidtweetresponse = raidtweet_pb2.RaidTweetResponse()
    async with websockets.connect(uri, subprotocols="binary", extra_headers=headers) as websocket:
        while True:
            _recv = await websocket.recv()
            if b"SNAPSHOT" in _recv:
                for arg in args[0]:
                    name = allraidboss_list[int(arg)]["translatedName"]
                    name_len = len(name.encode("utf-8"))
                    to_send = b"\x1a" + chr(name_len).encode("utf-8") + name.encode("utf-8")
                    await websocket.send(to_send)
            elif b'http' in _recv:
                raidtweetresponse.ParseFromString(_recv[3:])
                print(raidtweetresponse)


if len(sys.argv) > 0:
    asyncio.get_event_loop().run_until_complete(subscribe_boss(sys.argv[1:]))
else:
    asyncio.get_event_loop().run_until_complete(get_allraidboss())