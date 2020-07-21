import os
import json
import trio
from sys import stderr
from trio_websocket import open_websocket_url, HandshakeError
from contextlib import suppress
import random
import logging
import argparse


logger = logging.getLogger('fake_bus')
TICK = 0.1

def relaunch_on_disconnect(func):
    async def wrappers(*args, **kwargs):
        while True:
            try:
                await func(*args,**kwargs)
            except HandshakeError:
                logger.info("Doesn't Connect")
                await trio.sleep(5)
                logger.info('Relaunch')
    return wrappers


def load_routes(directory_path='routes'):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)



def generate_bus_id(route_id,bus_index,emulator_id):
    return f'{emulator_id}{route_id}-{bus_index}'

def create_description_route(bus_info,route,route_id,buses_per_route):
    random_position_bus = random.randint(0,len(route))
    random_route = route[random_position_bus:]
    for bus_index in range(buses_per_route):
        bus_info['busId'] = generate_bus_id(route_id,bus_index)
        for coordinates in random_route:
            lat, lng = coordinates
            bus_info['lat'] = lat
            bus_info['lng'] = lng
            yield bus_info

async def run_bus(route,route_id,buses_per_route,emulator_id,send_channel):
    bus_info = {
        "busId": None,
        "lat": None,
        "lng": None,
        "route": route_id,
    }
    async with send_channel:
        try:
            buses_info = create_description_route(bus_info,route,route_id,buses_per_route,emulator_id)
            for bus_info in buses_info:
                await send_channel.send(bus_info)
                await trio.sleep(TICK)
        except OSError as ose:
            logger.warning('Connection attempt failed: %s' % ose, file=stderr)



async def send_update(server_address,receive_channel):
    async with open_websocket_url(server_address) as ws:

        async with receive_channel:
            async for receive in receive_channel:
                await ws.send_message(json.dumps(receive))


@relaunch_on_disconnect
async def main():
    parser = argparse.ArgumentParser(description='List of options')
    parser.add_argument('--server', help='adress of server',default='ws://127.0.0.1:8080')
    parser.add_argument('-r',default=500, type=int,help='routes_number')
    parser.add_argument('--buses_per_route','-x',default=20,type=int,help='buses_per_route')
    parser.add_argument('--websockets_number','-w',default=10,type=int,help='websockets_number')
    parser.add_argument('--verbose','-v',action='count',help='Switch on logging')
    parser.add_argument('--emulator_id',default='',type=str)
    args = parser.parse_args()

    logging.basicConfig(level=args.verbose)
    server_address = args.server

    with suppress('KeyboardInterrupt'):
        async with trio.open_nursery() as nursery:
            send_channel, receive_channel = trio.open_memory_channel(0)
            async with send_channel, receive_channel:
                while True:
                    for route in load_routes()[0:args.r]:
                        route_id = route['name']
                        route = route['coordinates']

                        nursery.start_soon(
                                            run_bus, route, route_id,
                                            args.buses_per_route,args.emulator_id, send_channel.clone()
                        )
                        nursery.start_soon(send_update, server_address, receive_channel.clone())
                        await trio.sleep(TICK)


if __name__=='__main__':
    trio.run(main)

