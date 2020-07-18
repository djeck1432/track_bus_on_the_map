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
    return f'{route_id}-{bus_index}'


async def run_bus(route,bus_id,send_channel):

    bus_info = {
        "busId": bus_id,
        "lat": None,
        "lng": None,
        "route": bus_id,
    }
    async with send_channel:
        try:
            for coordinates in route:
                lat,lng = coordinates
                bus_info['lat'] = lat
                bus_info['lng'] = lng
                await send_channel.send(bus_info)
        except OSError as ose:
            print('Connection attempt failed: %s' % ose, file=stderr)


async def send_update(server_address,receive_channel):
    async with open_websocket_url(server_address) as ws:

        async with receive_channel:
            async for receive in receive_channel:
                await ws.send_message(json.dumps(receive))


async def main():
    server_address = 'ws://127.0.0.1:8080'
    async with trio.open_nursery() as nursery:
        send_channel, receive_channel = trio.open_memory_channel(0)
        async with send_channel, receive_channel:
            for route in load_routes():
                bus_id = route['name']
                route = route['coordinates']
                await trio.sleep(1)
                # random_position_route = random.randint(0,len(route))
                # print(type(random_position_route))
                # random_route = route[random_position_route:]

                nursery.start_soon(run_bus, route, bus_id, send_channel.clone())
                nursery.start_soon(send_update, server_address, receive_channel.clone())


if __name__=='__main__':
    trio.run(main)
