import trio
import json
from trio_websocket import serve_websocket, ConnectionClosed


async def echo_server(request):
    ws = await request.accept()
    while True:
        try:
            # message = await ws.get_message()
            message = {
                          "msgType": "newBounds",
                          "data": {
                            "east_lng": 37.65563964843751,
                            "north_lat": 55.77367652953477,
                            "south_lat": 55.72628839374007,
                            "west_lng": 37.54440307617188,
                          },
                        }
            await ws.send_message(json.dumps(message))
        except ConnectionClosed:
            break

async def main():
    await serve_websocket(echo_server, '127.0.0.1', 8000, ssl_context=None)

trio.run(main)
