#!/usr/bin/env python
import gevent.pywsgi, geventwebsocket.handler
import bottle, enum, geventwebsocket
import json, random, multiprocessing

def reset_deck():
    deck = []
    for rank in ["2", "3", "4", "5", "6", "7", "8", "9", "10", "j", "q", "k", "a"]:
        for suit in ["diams", "spades", "clubs", "hearts"]:
            deck.append(rank + ' ' + suit) # it's better if i don't get the "rank-" so i changed that
    return deck

def deal(num_of_players):
    deck = reset_deck()
    hands = [[] for x in range(num_of_players)]
    i = 0
    for _ in range((num_of_players * 7)):
        hands[i].append(random.choice(deck))
        deck.pop(deck.index(hands[i][-1]))
        i = (i + 1) % num_of_players
    return [deck, hands]

def has_card(hand: list, card_played: int):
    final = []
    last_find = 0
    for card in hand:
        if (card.split(' ')[0] == card_played.split(' ')[0]):
            final.append(hand.index(card, last_find))
            last_find = hand.index(card, last_find) + 1
    return final

class state(int, enum.Enum):
    DISCONNECTED        : int = 0
    CONNECTED           : int = 1
    READY_TO_START_GAME : int = 2
    PLAYING_GAME        : int = 3
    WAITING_FOR_OTHERS  : int = 4
    PLAYING             : int = 5
    END_OF_GAME         : int = 6
app = bottle.Bottle()
game_states = {
    'players_ready': {},
    'deck': None,
    'hands': None,
    'in_game': False,
    'matches': [],
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

# Reads game_states['deck']
# Writes game_states['deck', 'hands']
def go_fish(p_id):
    global game_states
    if (len(game_states['deck']) == 0):
        return False
    new_card_i = random.randint(0, len(game_states['deck']) - 1)
    game_states['hands'][p_id].append(game_states['deck'][new_card_i])
    game_states['deck'].pop(new_card_i)
    return True

# Reads game_states['num_of_players', 'players_ready']
def ready_to_play():
    global game_states
    for player in range(game_states['num_of_players']):
        if (game_states['players_ready'].get(player) != state.READY_TO_START_GAME):
            return False
    return True if (game_states['num_of_players'] > 0) else False

# Calls ready_to_play()
# Reads game_states['in_game']
# Writes game_states['deck', 'hands', 'in_game']
def start_game():
    global game_states
    if((ready_to_play()) and (not game_states['in_game'])):
        game_states['in_game'] = True
        dealt = deal(game_states['num_of_players'])
        game_states['deck'] = dealt[0]
        game_states['hands'] = dealt[1]
        game_states['matches'] = []
        return True
    return False

# Reads game_states['hands']
# Writes game_states['hands', 'matches']
# Calls has_card(hand, card_played)
def matches(p_id, card_played):
    global game_states
    index_in_hand = has_card(game_states['hands'][p_id], card_played.split(' ')[0])
    if (len(index_in_hand) == 4):
        game_states['matches'].append([p_id, card_played.split(' ')[0]])
        for i in range(len(index_in_hand) - 1, -1, -1):
            game_states['hands'][p_id].pop(index_in_hand[i])

# Reads game_states['player', 'hands', 'num_of_players']
# Writes game_states['hands', 'num_of_players']
# Calls go_fish() matches()
def play_card(p_id, card_played, p_to_ask):
    global game_states
    if (( game_states['player'] != p_id ) or ( not game_states['in_game'] )):
        return False

    if (not card_played in game_states['hands'][p_id]):
        return False
    
    index_of_all = has_card(game_states['hands'][p_to_ask], card_played)
    if (len(index_of_all) == 0):
        go_fish(p_id)

    for i in range(len(index_of_all) - 1, -1, -1):
        game_states['hands'][p_id].append(game_states['hands'][p_to_ask][index_of_all[i]])
        game_states['hands'][p_to_ask].pop(index_of_all[i])

    matches(p_id, card_played)
    game_states['player'] = (game_states['player'] + 1) % game_states['num_of_players']
    
    for hand in game_states['hands']:
        if (len(hand) == 0):
            game_states['in_game'] = False
    return True

def socket_task(ws, p_id):
    global game_states
    game_states['players_ready'][p_id] = state.CONNECTED
    while True:
        try:
            message = ws.receive() # BLOCKING CALL
        except:
            print("Failed to read Web Socket")
            return

        final = {
            'hand':             None,
            'other_hands':      None,
            'matches':          None,
            'state':            game_states['players_ready'].get(p_id),
        }

        if (message != 'PING' and message != None):
            try:
                message_json = json.loads(message)
            except:
                print("Problem converting to JSON. Message was", message)
                message_json = {}
        else:
            message_json = {}
        
        # print(f"Message {message}\n")
        if ( game_states['players_ready'].get(p_id) == state.CONNECTED ):
            if ( message_json.get('am_ready') == True ):
                message_json.pop('am_ready')
                game_states['players_ready'][p_id] = state.READY_TO_START_GAME
                final['state'] = game_states['players_ready'].get(p_id)

        if ( game_states['players_ready'].get(p_id) == state.READY_TO_START_GAME ):
            if ( message_json.get('am_ready') == False ):
                message_json.pop('am_ready')
                game_states['players_ready'][p_id] = state.CONNECTED
                final['state'] = game_states['players_ready'].get(p_id)
            start_game()
            if ( game_states['in_game'] == True):
                game_states['players_ready'][p_id] = state.PLAYING_GAME
                final['state'] = game_states['players_ready'].get(p_id)
            
        if ( game_states['players_ready'].get(p_id) == state.PLAYING_GAME ):
            if (game_states['player'] == p_id):
                final['state'] = state.PLAYING
                if (message_json.get('card_played') and message_json.get('player_asked')):
                    play_card(p_id, message_json.get('card_played'), message_json.get('player_asked'))
                    message_json.pop('card_played')
                    message_json.pop('player_asked')
                    final['state'] = state.WAITING_FOR_OTHERS

            elif (game_states['player'] != p_id):
                final['state'] = state.WAITING_FOR_OTHERS
            
            if (game_states['in_game'] == False):
                game_states['players_ready'][p_id] = state.CONNECTED
                final['state'] = game_states['players_ready'].get(p_id)
                ##### TODO ENDGAME Code here

            # print(f"Game States:\n{game_states}")
            final['hand'] = game_states["hands"][p_id]
            final['other_hands'] = get_other_hands(p_id)
            final['matches'] = game_states['matches']

        if (len(message_json)):
            print("UNUSED KEYS\n", message_json)

        try:
            ws.send(json.dumps(final))
        except:
            print("ERROR")
        finally:
            print(json.dumps(final))

@app.route("/websocket")
def handle_websocket():
    wsock = bottle.request.environ.get("wsgi.websocket")
    if not wsock:
        bottle.abort(400, "Expected WebSocket request.")
    game_states['num_of_players'] += 1
    thread = multiprocessing.Process(target=socket_task, args=(wsock, game_states['num_of_players']-1,), daemon=True)
    thread.start()

if __name__ == "__main__":
    server = gevent.pywsgi.WSGIServer(
        ("localhost", 5555), app, handler_class=geventwebsocket.handler.WebSocketHandler)
    server.serve_forever()
