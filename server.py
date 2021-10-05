#!/usr/bin/env python

import asyncio
import enum
import gevent.pywsgi
import geventwebsocket.handler
import geventwebsocket
import bottle
import enum

app = bottle.Bottle()

class state(enum.Enum):
    DISCONNECTED = 0
    CONNECTED = 1
    READY_TO_START_GAME = 2
    PLAYING_GAME = 3
    WAITING_FOR_OTHERS = 4
    PLAYING = 5
    END_OF_GAME = 6

async def socket_task(ws):
    counter = 0
    state_of_game = state.DISCONNECTED
    while True:
        message = ws.receive() # BLOCKING CALL
        if message is not "PING":
            if ( message == "INCIMENT" ):
                counter += 1
            elif ( message == "CONNECTED" ):
                state_of_game = state.CONNECTED
            elif ( message == "START" ):
                state_of_game = state.READY_TO_START_GAME
            elif ( message == "IN_GAME" ):
                state_of_game = state.PLAYING_GAME
            elif ( message == "OTHER_PLAYER" ):
                state_of_game = state.WAITING_FOR_OTHERS
            elif ( message == "PLAYING" ):
                state_of_game = state.PLAYING
            elif ( message == "END_OF_GAME" ):
                state_of_game = state.END_OF_GAME

            ws.send(str(state_of_game) + " " + str(counter))

@app.route('/websocket')
def handle_websocket():
    wsock = bottle.request.environ.get('wsgi.websocket')
    if not wsock:
        bottle.abort(400, 'Expected WebSocket request.')
    asyncio.run(socket_task(wsock))
    
if __name__ == '__main__':
    server = gevent.pywsgi.WSGIServer(
        ("localhost", 4444), app, handler_class=geventwebsocket.handler.WebSocketHandler)
    server.serve_forever()
