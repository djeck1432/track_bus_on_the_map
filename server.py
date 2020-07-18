import trio
import json
from functools import partial
import logging
from trio_websocket import serve_websocket, ConnectionClosed

buses = dict()
logger = logging.getLogger('server')


async def fetch_bus_info(request):
    ws = await request.accept()
    logger.debug('fetch bus info start')
    while True:
        try:
            message = await ws.get_message()
            format_changed_message = json.loads(message)
            bus_info = format_changed_message
            buses[bus_info['busId']] = bus_info
            await trio.sleep(1)
        except ConnectionClosed:
            logger.debug('fetch bus info start connection closed')
            break

async def listen_browser(ws):
    browser_message  = ws.get_message()
    print(f'browser_message:{browser_message}')
    await trio.sleep(1)



async def talk_to_browser(request):
    ws = await request.accept()
    logger.debug('talk to browser start')
    while True:
        for bus_id,bus_data in buses.items():
            bus_info = {
                "msgType": "Buses",
                "buses": bus_data
            }
            try:
                await ws.send_message(json.dumps(bus_info))
                await trio.sleep(1)
            except ConnectionClosed:
                logger.debug('talk to browser connection closed')
                break



async def fetch_info_server():
    await serve_websocket(fetch_bus_info,'127.0.0.1',8080,ssl_context=None)

async def send_info_server():
    await serve_websocket(talk_to_browser,'127.0.0.1', 8000, ssl_context=None)


async def main():
    logging.basicConfig(level=logging.DEBUG)
    async with trio.open_nursery() as nursery:
        nursery.start_soon(fetch_info_server)
        nursery.start_soon(send_info_server)



if __name__=='__main__':
    trio.run(main)
