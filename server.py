#!/usr/bin/env python
from http.client import parse_headers
from typing import Match
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

def has_card(hand, card_played):
    for card in hand:
        if card_played in card:
            return True
    return False

def final_all_index(cards, card_played):
    final = []
    for i in range(len(cards)):
        if (card_played in cards[i]):
            final.append(i)
    return final

app = bottle.Bottle()
player_states = {}
game_states = {
    'deck': None,
    'hands': None,
    'in_game': False,
    'matches': None,
    'num_of_players' : 0,
    'player': 0,
}

# Reads game_states['num_of_players', 'hands']
def get_other_hands(p_id):
    global game_states
    final = []
    for i in range(game_states['num_of_players']):
        if (i == p_id):
            continue
        final.append([i, len(game_states['hands'][i])])
    return final

# Reads game_states['num_of_players'] and player_states['state_of_game']
def ready_to_play():
    global game_states, player_states
    for player in range(game_states['num_of_players']):
        if (player_states[player]['state_of_game'] != state.READY_TO_START_GAME):
            return False
    return True

# Calls ready_to_play()
# Reads game_states['in_game']
# Writes game_states['deck', 'hands', 'in_game']
def start_game():
    global game_states
    if((ready_to_play()) and (not game_states['in_game'])):
        dealt = deal()
        game_states['deck'] = dealt[0]
        game_states['hands'] = dealt[1]
        game_states['in_game'] = True

# Read game_states['hands']
# Writes game_state['matches', 'hands']
# REWRITE WITH FUCTION CALLS
def matching(p_id):
    cards = []
    for i in range(len(game_states['hands'][p_id])):
        cards.append(game_states['hands'][p_id][i].split(' ').append(i))
    card_count = {}
    for card in cards:
        if (card[0] in card_count):
            card_count[card[0]][0] += 1
            card_count[card[0]][1].append(card[2])
        else:
            card_count[card[0]] = [1, [card[2]]]
    matches = []
    for card in card_count:
        if (card_count[card][0] == 4):
            matches.append(card)
    if (len(matches)):
        for match in matches:
            game_states['matches'].append([p_id, game_states['hands'][p_id][match[0]].split(' ')[0]])
            for i in match[1]:
                game_states['hands'][p_id].pop(i)

# Reads game_states['player', 'hands']
def play_card(p_id, card_played, p_to_ask):
    global game_states
    if (game_states['player'] != p_id):
        return False
    if (has_card(game_states['hands'][p_id], card_played)):
        return False
    if (has_card(game_states['hands'][p_to_ask], card_played)):
        index_of_all = final_all_index(game_states['hands'][p_to_ask], card_played)
        for i in index_of_all:
            game_states['hands'][p_id].append(game_states['hands'][p_to_ask][i])
            game_states['hands'][p_to_ask].pop(game_states['hands'][p_to_ask][i])
        matching(p_id)

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
                'hand':             None,
                'other_hands':      None,
                'matches':          None,
                'state':            player_states[p_id]['state_of_game'],
            }
            
            if ( player_states[p_id]['state_of_game'] == state.CONNECTED ):
                if ( message_json.get('am_ready') == True ):
                    message_json.pop('am_ready')
                    player_states[p_id]['state_of_game'] = state.READY_TO_START_GAME
                    final['state'] = player_states[p_id]['state_of_game']

            if ( player_states[p_id]['state_of_game'] == state.READY_TO_START_GAME ):
                if ( message_json.get('am_ready') == False ):
                    message_json.pop('am_ready')
                    player_states[p_id]['state_of_game'] = state.CONNECTED
                    final['state'] = player_states[p_id]['state_of_game']
                start_game()
                if ( game_states['in_game'] == True):
                    player_states[p_id]['state_of_game'] = state.PLAYING_GAME
                    final['state'] = player_states[p_id]['state_of_game']
                
            if ( player_states[p_id]['state_of_game'] == state.PLAYING_GAME ):
                if (game_states['in_game'] == False):
                    player_states[p_id]['state_of_game'] = state.CONNECTED
                    final['state'] = player_states[p_id]['state_of_game']
                    ##### TODO ENDGAME Code here

                elif (game_states['player'] == p_id):
                    final['state'] = state.PLAYING
                    if (message_json.get('card_played') and message_json.get('player_asked')):
                        play_card(p_id, message_json.get('card_played'), message_json.get('player_asked'))
                        final['state'] = state.WAITING_FOR_OTHERS
                    
                            

                elif (game_states['player'] != p_id):
                    final['state'] = state.WAITING_FOR_OTHERS
                
                final['hand'] = game_states[p_id]
                final['other_hands'] = get_other_hands(p_id)
                final['matches'] = game_states['matches']
                        
            if ( message_json == "INCIMENT" ):
                counter += 1

            ws.send(str(player_states[p_id]['state_of_game']) + ' ' + str(counter))

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
