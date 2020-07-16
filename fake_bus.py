import os
import json
import trio
from sys import stderr
from trio_websocket import open_websocket_url
import random




def load_routes(directory_path='routes'):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)

def generate_bus_id(route_id,bus_index):
    pass


async def run_bus(url,bus_id,route):
    bus_info = {
                "busId": bus_id,
                "lat": None,
                "lng": None,
                "route": "156"
            }
    try:
        async with open_websocket_url(url) as ws:
            for coordinates in route:
                lat,lng = coordinates
                bus_info['lat'] = lat
                bus_info['lng'] = lng
                await ws.send_message(json.dumps(bus_info,ensure_ascii=False))
    except OSError as ose:
        print('Connection attempt failed: %s' % ose, file=stderr)


async def main():
    url = 'ws://127.0.0.1:8080'
    async with trio.open_nursery() as nursery:
        send_channel, receive_channel = trio.open_memory_channel(0)
        async with send_channel, receive_channel:

            while True:
                for route in load_routes():
                    bus_id = route['name']
                    route = route['coordinates']

                    random_position_route = random.randint(0,len(route))
                    print(type(random_position_route))
                    random_route = route[random_position_route:]

                    nursery.start_soon(run_bus,url,bus_id,route)
                    nursery.start_soon(run_bus, url, bus_id, random_route)
                    await trio.sleep(0.1)

if __name__=='__main__':
    trio.run(main)
