#!/usr/bin/env python

import asyncio
import enum
import gevent.pywsgi
import geventwebsocket.handler
import geventwebsocket
import bottle
import enum
import json

app = bottle.Bottle()

class state(enum.Enum):
    DISCONNECTED = 0
    CONNECTED = 1
    READY_TO_START_GAME = 2
    PLAYING_GAME = 3
    WAITING_FOR_OTHERS = 4
    PLAYING = 5
    END_OF_GAME = 6

player_states = {}
num_of_players = 0
playing_game = False

async def socket_task(ws, p_id):
    global num_of_players, player_states, playing_game
    counter = 0
    state_of_game = state.DISCONNECTED
    is_json = False
    while True:
        message = ws.receive() # BLOCKING CALL
        if (message != "PING" and message != None):
            if (message[0] == "1"):
                json.loads(message[1:])
                is_json = True
            else:
                is_json = False

            if ( message == "CONNECTED" ):
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
            elif ( message == "INCIMENT" ):
                counter += 1

            ws.send(str(state_of_game) + " " + str(counter))

@app.route('/websocket')
def handle_websocket():
    global num_of_players, player_states
    wsock = bottle.request.environ.get('wsgi.websocket')
    if not wsock:
        bottle.abort(400, 'Expected WebSocket request.')
    player_states[num_of_players] = []
    num_of_players += 1
    asyncio.run(socket_task(wsock, num_of_players-1))
    
if __name__ == '__main__':
    server = gevent.pywsgi.WSGIServer(
        ("localhost", 4444), app, handler_class=geventwebsocket.handler.WebSocketHandler)
    server.serve_forever()
