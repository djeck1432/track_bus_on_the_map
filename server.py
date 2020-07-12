import trio
import json
import requests
from trio_websocket import serve_websocket, ConnectionClosed


def fetch_coordinates_route(url):
    response = requests.get(url)
    response.raise_for_status()
    coordinates = response.json()['coordinates']
    return coordinates

async def echo_server(request):
    bus_info = {
        "msgType": "Buses",
        "buses": [
            {"busId": "c790сс", "lat": 55.7500, "lng": 37.600, "route": "120"},
            {"busId": "a134aa", "lat": 55.7494, "lng": 37.621, "route": "670к"},
        ]
    }
    coordinates = fetch_coordinates_route('https://dvmn.org/media/filer_public/aa/10/aa10aaf5-047f-49d6-a7a9-78f98b092161/156.json')
    ws = await request.accept()
    while True:
        for coordinate in coordinates:
            bus_info['buses'][0]['lat'] = coordinate[0]
            bus_info['buses'][0]['lng'] = coordinate[1]
            try:
                await ws.send_message(json.dumps(bus_info))
                await trio.sleep(1)
            except ConnectionClosed:
                break

async def main():
    await serve_websocket(echo_server, '127.0.0.1', 8000, ssl_context=None)

trio.run(main)
