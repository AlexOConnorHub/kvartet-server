#!/usr/bin/env python
import gevent.pywsgi, geventwebsocket.handler
import asyncio, bottle, enum
import geventwebsocket, json, random
class state(enum.Enum):
    DISCONNECTED = 0
    CONNECTED = 1
    READY_TO_START_GAME = 2
    PLAYING_GAME = 3
    WAITING_FOR_OTHERS = 4
    PLAYING = 5
    END_OF_GAME = 6

def reset_deck():
    deck = []
    for card in ["rank-2", "rank-3", "rank-4", "rank-5", "rank-6", "rank-7", "rank-8", "rank-9", "rank-j", "rank-q", "rank-k", "rank-a"]:
        for suit in ["diams", "spades", "clubs", "hearts"]:
            deck.append(card + ' ' + suit)
    return deck

def deal(num_of_players):
    deck = reset_deck()
    hands = [[] for x in range(num_of_players)]
    for i in range((num_of_players * 7)):
        hands[i].append(random.choice(deck))
        deck.pop(deck.index(hands[i]))
        i = (i + 1) % num_of_players
    return [deck, hands]

app = bottle.Bottle()
player_states = {}
game_states = {
    'deck': None,
    'hands': None,
    'in_game': False,
    'num_of_players' : 0,
    'player': 0,
}

def ready_to_play(): # Uses game_states and player_states
    for player in range(game_states['num_of_players']):
        if (player_states[player]['state_of_game'] != state.READY_TO_START_GAME):
            return False
    return True

def game_update(p_id):
    global player_states, game_states
    if (game_states['in_game']):
        pass
    elif(ready_to_play()):
        dealt = deal()
        game_states['deck'] = dealt[0]
        game_states['hands'] = dealt[1]
        game_states['in_game'] = True

async def socket_task(ws, p_id):
    global game_states, player_states
    counter = 0
    player_states[p_id]['state_of_game'] = state.CONNECTED
    while True:
        message = ws.receive() # BLOCKING CALL
        if (message != 'PING' and message != None):
            try:
                message_json = json.loads(message)
            except:
              print("Problem converting to JSON. Message was", message)
              continue

            final = {
                'ack':              [None, False],
                'change_of_state':  False,
                'hand':             False,
                'other_hands':      False,
                'matches':          [],
                'state':            player_states[p_id]['state_of_game'],
            }
            
            if ( player_states[p_id]['state_of_game'] == state.CONNECTED ):
                if ( message_json.get('am_ready') == True ):
                    message_json.pop('am_ready')
                    player_states[p_id]['state_of_game'] = state.READY_TO_START_GAME
                    final['change_of_state'] =  True
                    final['ack'] = ['am_ready', True]

            elif ( player_states[p_id]['state_of_game'] == state.READY_TO_START_GAME ):
                if ( game_states['in_game'] == False):
                    player_states[p_id]['state_of_game'] = state.PLAYING_GAME
                    final['change_of_state'] = True
                elif ( message_json.get('am_ready') == False ):
                    message_json.pop('am_ready')
                    player_states[p_id]['state_of_game'] = state.CONNECTED
                    final['change_of_state'] =  True
                    final['ack'] = ['am_ready', True]


            elif ( player_states[p_id]['state_of_game'] == state.PLAYING_GAME ):
                player_states[p_id]['state_of_game'] = state.PLAYING_GAME

            elif ( player_states[p_id]['state_of_game'] == state.WAITING_FOR_OTHERS ):
                player_states[p_id]['state_of_game'] = state.WAITING_FOR_OTHERS
            
            elif ( player_states[p_id]['state_of_game'] == state.PLAYING ):
                player_states[p_id]['state_of_game'] = state.PLAYING
            
            elif ( player_states[p_id]['state_of_game'] == state.PLAYING ):
                player_states[p_id]['state_of_game'] = state.END_OF_GAME
            
            elif ( message_json == "INCIMENT" ):
                counter += 1

            final['state'] = player_states[p_id]['state_of_game']
            ws.send(str(player_states[p_id]['state_of_game']) + ' ' + str(counter))
            game_update()

@app.route("/websocket")
def handle_websocket():
    global player_states
    wsock = bottle.request.environ.get("wsgi.websocket")
    if not wsock:
        bottle.abort(400, "Expected WebSocket request.")
    player_states[game_states['num_of_players']] = {}
    game_states['num_of_players'] += 1
    asyncio.run(socket_task(wsock, game_states['num_of_players']-1))
    
if __name__ == "__main__":
    server = gevent.pywsgi.WSGIServer(
        ("localhost", 4444), app, handler_class=geventwebsocket.handler.WebSocketHandler)
    server.serve_forever()
