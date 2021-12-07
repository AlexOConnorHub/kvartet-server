#!/usr/bin/env python
import gevent.pywsgi, geventwebsocket.handler
import bottle, enum, geventwebsocket
import json, random

def reset_deck():
    deck = []
    for rank in ["2", "3", "4", "5", "6", "7", "8", "9", "10", "j", "q", "k", "a"]:
        for suit in ["diams", "spades", "clubs", "hearts"]:
            deck.append(rank + ' ' + suit) 
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
    'last_play': {}
}
known_players = {}

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
        return None
    new_card_i = random.randint(0, len(game_states['deck']) - 1)
    game_states['hands'][p_id].append(game_states['deck'][new_card_i])
    game_states['deck'].pop(new_card_i)
    return game_states['hands'][p_id][-1]

# Reads game_states['num_of_players', 'players_ready']
def ready_to_play():
    global game_states
    for player in range(game_states['num_of_players']):
        if (game_states['players_ready'].get(player) != state.READY_TO_START_GAME):
            return False
    return True if (game_states['num_of_players'] > 1) else False

# Calls ready_to_play()
# Reads game_states['in_game']
# Writes game_states['deck', 'hands', 'in_game', 'player']
def start_game():
    global game_states
    if((ready_to_play()) and (not game_states['in_game'])):
        game_states['in_game'] = True
        dealt = deal(game_states['num_of_players'])
        game_states['deck'] = dealt[0]
        game_states['hands'] = dealt[1]
        game_states['matches'] = []
        game_states['player'] = 0
        return True
    return False

# Reads known_players, game_states['num_of_players', 'in_game']
# Writes known_players, game_states['num_of_players']
def new_player(UUID):
    global known_players, game_states
    if ((known_players.get(UUID) == None) and not game_states['in_game']):
        known_players[UUID] = game_states['num_of_players']
        game_states['num_of_players'] += 1
    return known_players.get(UUID)

# Reads game_states['hands']
# Writes game_states['hands', 'matches']
# Calls has_card(hand, card_played)
def matches(p_id, card_played):
    global game_states
    if (card_played == None):
        return
    index_in_hand = has_card(game_states['hands'][p_id], card_played.split(' ')[0])
    if (len(index_in_hand) == 4):
        game_states['matches'].append([p_id, card_played.split(' ')[0]])
        for i in range(len(index_in_hand) - 1, -1, -1):
            game_states['hands'][p_id].pop(index_in_hand[i])

def valid_play(p_id, card_played):
    global game_states
    for suit in ["diams", "spades", "clubs", "hearts"]:
        if (" ".join([card_played.split(" ")[0], suit]) in game_states['hands'][p_id]):
            return True
    return False

# Reads game_states['player', 'hands', 'num_of_players']
# Writes game_states['hands', 'num_of_players', 'player', 'last_play']
# Calls go_fish() matches()
def play_card(p_id, card_played, p_to_ask):
    global game_states
    if (( game_states['player'] != p_id ) or ( not game_states['in_game'] )):
        return
    if (not valid_play(p_id, card_played)):
        return
    game_states['last_play'] = {
        'card_asked_for' : card_played,
        'player_asked'   : p_to_ask,
        'player_asking'  : p_id,
        'success'        : False
    }
    if (not (card_played in game_states['hands'][p_to_ask])): # Not in hand
        new_card = go_fish(p_id)
        if (new_card != card_played):
            game_states['player'] = (game_states['player'] + 1) % game_states['num_of_players']
        matches(p_id, new_card)
    else:
        game_states['hands'][p_id].append(card_played)
        game_states['hands'][p_to_ask].remove(card_played)
        matches(p_id, card_played)
        game_states['last_play']['success'] = True

    if player_won():
        print("we have a winner!")
        game_states['in_game'] = False

# Czechs if any player has won yet
# Reads game_states['matches', 'num_of_players']
def player_won():
    global game_states
    threshold = 7
    if len(game_states["matches"]) == 13:
        return True
    for player in range(game_states['num_of_players']):
        players_matches = 0
        for match in game_states["matches"]:
            if (match[0] == player):
                players_matches += 1
        if players_matches >= threshold:
            return True
    return False

def socket_task(ws, p_id):
    global game_states
    while True:
        try:
            message = ws.receive() # BLOCKING CALL
        except:
            print("Failed to read Web Socket")
            return

        final = {
            'hand'        : None,
            'other_hands' : None,
            'matches'     : None,
            'state'       : game_states['players_ready'].get(p_id),
            'p_id'        : p_id,
            'last_play'   : {}
        }

        if (message != 'PING' and message != None):
            try:
                message_json = json.loads(message)
            except:
                print("Problem converting to JSON. Message was", message)
                message_json = {}
        else:
            message_json = {}
        
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
            
        if (( game_states['players_ready'].get(p_id) == state.PLAYING_GAME)):

            if ((len(game_states['hands'][p_id]) == 0) and game_states['player'] == p_id):
                game_states['player'] = (game_states['player'] + 1) % game_states['num_of_players']
            if (game_states['player'] == p_id):
                final['state'] = state.PLAYING
                if (message_json.get('card_played') and (message_json.get('player_asked') != None)):
                    play_card(p_id, message_json.get('card_played'), message_json.get('player_asked'))
                    message_json.pop('card_played')
                    message_json.pop('player_asked')

            if (game_states['player'] != p_id):
                final['state'] = state.WAITING_FOR_OTHERS
            
            if (game_states['in_game'] == False):
                game_states['players_ready'][p_id] = state.CONNECTED
                final['state'] = game_states['players_ready'].get(p_id)

            final['other_hands'] = get_other_hands(p_id)
            final['matches']     = game_states['matches']
            final['last_play']   = game_states['last_play']
            final['hand']        = game_states["hands"][p_id]
            final['hand'].sort()

        if (len(message_json)):
            print("UNUSED KEYS\n", message_json)

        try:
            ws.send(json.dumps(final))
        except:
            print("ERROR")
            print(json.dumps(final))

@app.route("/websocket/<UUID>")
def handle_websocket(UUID=None):
    wsock = bottle.request.environ.get("wsgi.websocket")
    if not wsock:
        bottle.abort(400, "Expected WebSocket request.")
    if ((game_states['num_of_players'] > 4) or (UUID == None)):
        return
    print(UUID)
    p_id = new_player(UUID)
    if (p_id == None):
        return
    if (game_states['players_ready'].get(p_id) == None):
        game_states['players_ready'][p_id] = state.CONNECTED
    socket_task(wsock, p_id)

if __name__ == "__main__":
    server = gevent.pywsgi.WSGIServer(
        ("localhost", 4444), app, handler_class=geventwebsocket.handler.WebSocketHandler)
    server.serve_forever()
