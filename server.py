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

def game_update():
    pass

player_states = {}
num_of_players = 0
playing_game = False

async def socket_task(ws, p_id):
    global num_of_players, player_states, playing_game
    counter = 0
    player_states[p_id]["state_of_game"] = state.CONNECTED
    while True:
        message = ws.receive() # BLOCKING CALL
        if (message != "PING" and message != None):
            final = {
                'change_of_state':  False,
                'ack':              False,
                'state':            player_states[p_id]["state_of_game"]
            }
            message_json = json.loads(message[1:])
            if ( player_states[p_id]["state_of_game"] == state.CONNECTED ):
                if ( message_json["am_ready"] == True ):
                    player_states[p_id]["state_of_game"] = state.READY_TO_START_GAME
                    final['ack'] = True
            elif ( player_states[p_id]["state_of_game"] == state.READY_TO_START_GAME ):
                if ( playing_game == True):
                    player_states[p_id]["state_of_game"] = state.PLAYING_GAME
                    final['change_of_state'] = True
            elif ( player_states[p_id]["state_of_game"] == state.PLAYING_GAME ):
                player_states[p_id]["state_of_game"] = state.PLAYING_GAME
            elif ( player_states[p_id]["state_of_game"] == state.WAITING_FOR_OTHERS ):
                player_states[p_id]["state_of_game"] = state.WAITING_FOR_OTHERS
            elif ( player_states[p_id]["state_of_game"] == state.PLAYING ):
                player_states[p_id]["state_of_game"] = state.PLAYING
            elif ( player_states[p_id]["state_of_game"] == "END_OF_GAME" ):
                player_states[p_id]["state_of_game"] = state.END_OF_GAME
            elif ( message_json == "INCIMENT" ):
                counter += 1

            final['state'] = player_states[p_id]["state_of_game"]
            ws.send(str(player_states[p_id]["state_of_game"]) + " " + str(counter))
            game_update()

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
