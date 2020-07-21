import trio
import json
from functools import partial
import logging
from trio_websocket import serve_websocket, ConnectionClosed
from dataclasses import dataclass
from contextlib import suppress


buses = dict()
logger = logging.getLogger('server')
bounds = None
TICK = 0.1


@dataclass
class Bus:
    busId: str
    lat: float
    lng: float
    route: str


@dataclass
class WindowBus:
    south_lat: float
    north_lat: float
    west_lng: float
    east_lng: float
    valid_lng: bool = False
    valid_lat: bool = False

    def is_inside(self,lat,lng):
        if self.south_lat > lat < self.north_lat:
            self.valid_lat = True
        if self.west_lng > lng < self.east_lng:
            self.valid_lng = True
        if self.valid_lng + self.east_lng == 2:
            return True



def is_inside(bounds,lat,lng):
    valid_lng = False
    valid_lat = False
    if bounds['south_lat'] >= lat <= bounds['north_lat']:
        valid_lat = True
    if bounds['west_lng'] >= lng <= bounds['east_lng']:
        valid_lng = True
    if valid_lat + valid_lng == 2:
        return True


async def fetch_bus_info(request):
    ws = await request.accept()
    logger.debug('fetch_bus_info start')
    while True:
        try:
            message = await ws.get_message()
            format_changed_message = json.loads(message)
            bus = format_changed_message
            bus_info = Bus(bus['busId'],bus['lat'],bus['lng'],bus['route'])
            buses[bus_info['busId']] = bus_info
            await trio.sleep(TICK)
        except ConnectionClosed:
            logger.debug('fetch_bus_info connection closed')
            break


async def listen_browser(ws):
    try:
        browser_message = await ws.get_message()
        print(f'browser_message:{browser_message}')
        formated_message = json.loads(browser_message)
        global bounds
        bounds = formated_message['data']
    except ConnectionClosed:
        logger.warning('ConnectionClosed')

async def send_browser(ws,bus_info):
    frontend_format = json.dumps(bus_info)
    try:
        await ws.send_message(frontend_format)
    except ConnectionClosed:
        logger.warning('ConnectionClosed')

async def send_buses(ws,copy_buses): #FIXME
    #TODO переименовать copy_buses
    #TODO уточнить какой bounds сейчас работает
    buses_data = []
    global bounds
    for bus_id, bus_data in copy_buses.items():
        lat = bus_data['lat']
        lng = bus_data['lng']
        if is_inside(bounds, lat, lng):
            buses_data.append(bus_data)
    bus_info = {
        "msgType": "Buses",
        "buses": buses_data
    }
    await ws.send_message(json.dumps(bus_info))



async def talk_to_browser(request):
    ws = await request.accept()
    logger.debug('talk_to_browser start')
    while True:
        copy_buses = buses.copy()
        buses_data = []
        for bus_id, bus_data in copy_buses.items():
            buses_data.append(bus_data)
        bus_info = {
            "msgType": "Buses",
            "buses": buses_data
        }
        try:
            async with trio.open_nursery() as nursery:
                nursery.start_soon(listen_browser,ws)
                nursery.start_soon(send_browser,ws,bus_info)
                nursery.start_soon(send_buses,ws,copy_buses)
        except ConnectionClosed:
            logger.debug('talk_to_browser connection closed')
            break
        await trio.sleep(TICK)



async def fetch_info_server():
    await serve_websocket(fetch_bus_info,'127.0.0.1',8080,ssl_context=None)


async def send_info_server():
    await serve_websocket(talk_to_browser,'127.0.0.1', 8000, ssl_context=None)


async def main():
    with suppress('KeyboardInterrupt'):
        logging.basicConfig(level=logging.DEBUG)
        async with trio.open_nursery() as nursery:
            nursery.start_soon(fetch_info_server)
            nursery.start_soon(send_info_server)



if __name__=='__main__':
    trio.run(main)

