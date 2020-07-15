import trio
import json
import requests
from trio_websocket import serve_websocket, ConnectionClosed

buses = []

async def fetch_route_server(request):
    print('ok start')
    ws = await request.accept()
    print('ok1')
    while True:
            try:
                message = await ws.get_message()
                print(message)

                await trio.sleep(1)
            except ConnectionClosed:
                break

async def talk_to_browser(request):
    ws = await request.accept()
    while True:

            try:
                await ws.send_message(json.dumps(bus_info))
                await trio.sleep(1)
            except ConnectionClosed:
                break

async def main():
    await serve_websocket(fetch_route_server, '127.0.0.1', 8080, ssl_context=None)
    await serve_websocket(talk_to_browser, '127.0.0.1', 8000, ssl_context=None)

trio.run(main)
