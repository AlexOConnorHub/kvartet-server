import unittest
from server import *
FULL_DECK = [
                '2 diams'  , '2 spades', '2 clubs', '2 hearts',
                '3 diams'  , '3 spades', '3 clubs', '3 hearts',
                '4 diams'  , '4 spades', '4 clubs', '4 hearts',
                '5 diams'  , '5 spades', '5 clubs', '5 hearts',
                '6 diams'  , '6 spades', '6 clubs', '6 hearts',
                '7 diams'  , '7 spades', '7 clubs', '7 hearts',
                '8 diams'  , '8 spades', '8 clubs', '8 hearts',
                '9 diams'  , '9 spades', '9 clubs', '9 hearts',
                '10 diams' , '10 spades','10 clubs','10 hearts',
                'j diams'  , 'j spades', 'j clubs', 'j hearts',
                'q diams'  , 'q spades', 'q clubs', 'q hearts',
                'k diams'  , 'k spades', 'k clubs', 'k hearts',
                'a diams'  , 'a spades', 'a clubs', 'a hearts'
            ]
class TestNoPublicVariables(unittest.TestCase):
    def test_reset_deck(self): 
        reset_deck_return = reset_deck()
        for card in FULL_DECK:
            self.assertTrue(card in reset_deck_return)
        self.assertEqual(len(reset_deck())      , 52)
        self.assertTrue(isinstance(reset_deck() , list))

    def test_deal(self):
        self.assertTrue(isinstance(deal(2)    , list))
        self.assertTrue(isinstance(deal(3)[0] , list))
        self.assertTrue(isinstance(deal(4)[1] , list))
        sumOfAll = deal(3)
        self.assertEqual(
            (
                len(sumOfAll[0]) + 
                len(sumOfAll[1][0]) + 
                len(sumOfAll[1][1]) + 
                len(sumOfAll[1][2])
            ), 
            52
        )
        backTogether = (sumOfAll[0]) + (sumOfAll[1][0]) + (sumOfAll[1][1]) + (sumOfAll[1][2])
        backTogether.sort()
        sortedDeck = FULL_DECK
        sortedDeck.sort()
        self.assertEqual(backTogether, sortedDeck)

    def test_has_card(self):
        self.assertTrue(isinstance( has_card([], ""), list))
        self.assertEqual(len(has_card([], "")), 0)
        self.assertEqual(len(has_card(["1", "2"], "1")), 1)
        self.assertEqual(len(has_card(["1", "1", "2"], "1")), 2)
        hand = [
            '2 diams', '3 diams', '4 diams', '5 diams',
            '6 diams', '6 spades', '7 diams', '7 spades',
        ]
        self.assertEqual(has_card(hand, "a"), [])
        self.assertEqual(has_card(hand, "2"), [0])
        self.assertEqual(has_card(hand, "5"), [3])
        self.assertEqual(has_card(hand, "7"), [6,7])

class TestPublicVariables(unittest.TestCase):
    # Reads game_states['num_of_players', 'hands']
    def test_get_other_hands(self):
        global game_states
        game_states['num_of_players'] = 3
        game_states['hands'] = [
            ['2 diams', '2 spades'], 
            ['3 diams', '3 spades', '3 clubs'], 
            ['4 diams', '4 spades', '4 clubs', '4 hearts']
        ]
        self.assertTrue(isinstance(get_other_hands(2), list))
        self.assertTrue(isinstance(get_other_hands(2)[0], list))
        self.assertTrue(isinstance(get_other_hands(2)[1], list))
        self.assertEqual(get_other_hands(2), [[0, 2], [1, 3]])

    # Reads game_states['deck']
    # Writes game_states['deck', 'hands']
    def test_go_fish(self):
        global game_states
        game_states['num_of_players'] = 3
        game_states['deck'] = ['5 diams']

        game_states['hands'] = [
            ['2 diams', '2 spades'], 
            ['3 diams', '3 spades', '3 clubs'], 
            ['4 diams', '4 spades', '4 clubs', '4 hearts']
        ]
        go_fish(2)
        self.assertTrue('5 diams' in game_states['hands'][2])
        self.assertEqual(game_states['deck'], [])
        self.assertFalse(go_fish(2))
        
    def test_ready_to_play(self):
        global game_states
        game_states['num_of_players'] = 3
        game_states['players_ready'] = {}
        self.assertTrue(isinstance(ready_to_play(), bool))
        self.assertFalse(ready_to_play())
        game_states['players_ready'][0] = state.READY_TO_START_GAME
        game_states['players_ready'][1] = state.CONNECTED
        self.assertFalse(ready_to_play())
        game_states['players_ready'][2] = state.READY_TO_START_GAME
        self.assertFalse(ready_to_play())
        game_states['players_ready'][1] = state.READY_TO_START_GAME
        self.assertTrue(ready_to_play())

    # Calls ready_to_play()
    # Reads game_states['in_game']
    # Writes game_states['deck', 'hands', 'in_game']
    def test_start_game(self):
        global game_states
        game_states['in_game'] = False
        game_states['num_of_players'] = 3
        game_states['players_ready'] = {
            0: state.READY_TO_START_GAME, 
            1: state.READY_TO_START_GAME
        }
        self.assertTrue(isinstance(start_game(), bool))
        self.assertFalse(start_game())
        game_states['players_ready'][2] = state.READY_TO_START_GAME
        self.assertTrue(ready_to_play())
        self.assertTrue(start_game())
        self.assertTrue(game_states['in_game'])
        self.assertEqual(len(game_states['deck']), 31)
        self.assertEqual(len(game_states['hands']), 3)
        self.assertEqual(len(game_states['hands'][0]), 7)
        backTogether = (game_states['deck']) + (game_states['hands'][0]) + (game_states['hands'][1]) + (game_states['hands'][2])
        backTogether.sort()
        sortedDeck = FULL_DECK
        sortedDeck.sort()
        self.assertEqual(backTogether, sortedDeck)

    
    # Reads game_states['hands']
    # Writes game_states['hands', 'matches']
    def test_matches(self):
        global game_states
        game_states['hands'] = [
            ['2 diams', '2 spades'], 
            ['3 diams', '3 spades', '3 clubs', '3 hearts'], 
            ['4 diams', '4 spades', '4 clubs', '4 hearts'],
            ['5 diams', '5 spades', 'j clubs', '5 clubs', '5 hearts'],
            ['6 diams', '6 spades', '6 clubs', 'a diams', 'a clubs', '6 hearts'],
        ]
        matches(0, '2 diams')
        self.assertEqual(len(game_states['matches']), 0)
        self.assertEqual(len(game_states['hands'][0]), 2)
        self.assertEqual(game_states['hands'][0], ['2 diams', '2 spades'])
        matches(1, '3 diams')
        self.assertEqual(len(game_states['matches']), 1)
        self.assertEqual(game_states['matches'], [[1, '3']])
        self.assertEqual(len(game_states['hands'][1]), 0)
        self.assertEqual(game_states['hands'][1], [])
        matches(2, '4 diams')
        self.assertEqual(len(game_states['matches']), 2)
        self.assertEqual(game_states['matches'], [[1, '3'], [2, '4']])
        self.assertEqual(len(game_states['hands'][2]), 0)
        self.assertEqual(game_states['hands'][2], [])
        matches(3, '5 diams')
        self.assertEqual(len(game_states['matches']), 3)
        self.assertEqual(game_states['matches'], [[1, '3'], [2, '4'], [3, '5']])
        self.assertEqual(len(game_states['hands'][3]), 1)
        self.assertEqual(game_states['hands'][3], ['j clubs'])
        matches(4, '6 diams')
        self.assertEqual(len(game_states['matches']), 4)
        self.assertEqual(game_states['matches'], [[1, '3'], [2, '4'], [3, '5'], [4, '6']])
        self.assertEqual(len(game_states['hands'][4]), 2)
        self.assertEqual(game_states['hands'][4], ['a diams', 'a clubs'])
        
    # Reads game_states['player', 'hands']
    # Writes game_states['hands']
    # Calls go_fish() matches()
    def test_play_card(self):
        global game_states
        game_states['num_of_players'] = 3
        game_states['in_game'] = True
        game_states['matches'] = []
        game_states['deck'] = []
        game_states['hands'] = [
            ['2 diams', '4 diams', '3 clubs', '2 hearts', 'a clubs'],
            ['3 diams', '3 spades', '2 clubs', '4 hearts', 'a spades'], 
            ['2 spades', '4 spades', '4 clubs', '3 hearts', 'a diams'],
        ]
        game_states['player'] = 0
        play_card(0, '2 clubs', 1)
        game_states['player'] = 1
        play_card(1, '3 clubs', 0)
        game_states['player'] = 2
        play_card(2, '4 diams', 0)
        self.assertEqual(game_states['hands'][0], ['2 diams', '2 hearts', 'a clubs', '2 clubs'])
        self.assertEqual(game_states['hands'][1], ['3 diams', '3 spades', '4 hearts', 'a spades', '3 clubs'])
        self.assertEqual(game_states['hands'][2], ['2 spades', '4 spades', '4 clubs', '3 hearts', 'a diams', '4 diams'])
        game_states['player'] = 0
        play_card(0, '2 spades', 2)
        game_states['player'] = 1
        play_card(1, '3 hearts', 2)
        game_states['player'] = 2
        play_card(2, '4 hearts', 1)
        self.assertEqual(game_states['hands'][0], ['a clubs'])
        self.assertEqual(game_states['hands'][1], ['a spades'])
        self.assertEqual(game_states['hands'][2], ['a diams'])
        self.assertEqual(game_states['matches'],  [[0, '2'], [1, '3'], [2, '4']])
        game_states['player'] = 0
        play_card(0, '2 spades', 2)
        self.assertEqual(game_states['player'], 1)
        play_card(1, '2 spades', 2)
        self.assertEqual(game_states['player'], 2)
        


    # Reads known_players, game_states['num_of_players']
    # Writes known_players, game_states['num_of_players']
    def test_new_player(self):
        global game_states
        game_states['num_of_players'] = 0
        self.assertEqual(0, game_states['num_of_players'])
        self.assertEqual(0, new_player("FIRST PLAYER"))
        self.assertEqual(1, game_states['num_of_players'])
        self.assertEqual(0, new_player("FIRST PLAYER"))
        self.assertEqual(1, game_states['num_of_players'])
        self.assertEqual(1, new_player("SECCOND PLAYER"))
        self.assertEqual(2, game_states['num_of_players'])
        self.assertEqual(0, new_player("FIRST PLAYER"))
        self.assertEqual(2, game_states['num_of_players'])
        self.assertEqual(1, new_player("SECCOND PLAYER"))
        self.assertEqual(2, game_states['num_of_players'])
        self.assertEqual(2, new_player("THIRD PLAYER"))
        self.assertEqual(3, game_states['num_of_players'])
        self.assertEqual(0, new_player("FIRST PLAYER"))
        self.assertEqual(3, game_states['num_of_players'])
        self.assertEqual(1, new_player("SECCOND PLAYER"))
        self.assertEqual(3, game_states['num_of_players'])
        self.assertEqual(2, new_player("THIRD PLAYER"))
        self.assertEqual(3, game_states['num_of_players'])


if __name__ == '__main__':
    unittest.main()