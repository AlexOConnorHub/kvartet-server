import unittest
from server import *
FULL_DECK = [
                'rank-2 diams'  , 'rank-2 spades', 'rank-2 clubs', 'rank-2 hearts',
                'rank-3 diams'  , 'rank-3 spades', 'rank-3 clubs', 'rank-3 hearts',
                'rank-4 diams'  , 'rank-4 spades', 'rank-4 clubs', 'rank-4 hearts',
                'rank-5 diams'  , 'rank-5 spades', 'rank-5 clubs', 'rank-5 hearts',
                'rank-6 diams'  , 'rank-6 spades', 'rank-6 clubs', 'rank-6 hearts',
                'rank-7 diams'  , 'rank-7 spades', 'rank-7 clubs', 'rank-7 hearts',
                'rank-8 diams'  , 'rank-8 spades', 'rank-8 clubs', 'rank-8 hearts',
                'rank-9 diams'  , 'rank-9 spades', 'rank-9 clubs', 'rank-9 hearts',
                'rank-10 diams' , 'rank-10 spades','rank-10 clubs','rank-10 hearts',
                'rank-j diams'  , 'rank-j spades', 'rank-j clubs', 'rank-j hearts',
                'rank-q diams'  , 'rank-q spades', 'rank-q clubs', 'rank-q hearts',
                'rank-k diams'  , 'rank-k spades', 'rank-k clubs', 'rank-k hearts',
                'rank-a diams'  , 'rank-a spades', 'rank-a clubs', 'rank-a hearts'
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
        self.assertAlmostEqual(backTogether, sortedDeck)

    def test_has_card(self):
        self.assertTrue(isinstance( has_card([], ""), list))
        self.assertEqual(len(has_card([], "")), 0)
        self.assertEqual(len(has_card(["1", "2"], "1")), 1)
        self.assertEqual(len(has_card(["1", "1", "2"], "1")), 2)
        hand = [
            'rank-2 diams', 'rank-3 diams' , 'rank-4 diams', 'rank-5 diams',
            'rank-6 diams', 'rank-6 spades', 'rank-7 diams', 'rank-7 spades',
        ]
        self.assertEqual(has_card(hand, "rank-a"), [])
        self.assertEqual(has_card(hand, "rank-2"), [0])
        self.assertEqual(has_card(hand, "rank-5"), [3])
        self.assertEqual(has_card(hand, "rank-7"), [6,7])

class TestPublicVariables(unittest.TestCase):
    # Reads game_states['num_of_players', 'hands']
    def test_get_other_hands(self):
        global game_states
        game_states['num_of_players'] = 3
        game_states['hands'] = [
            ['rank-2 diams'  , 'rank-2 spades'], 
            ['rank-3 diams'  , 'rank-3 spades', 'rank-3 clubs'], 
            ['rank-4 diams'  , 'rank-4 spades', 'rank-4 clubs', 'rank-4 hearts']
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
        game_states['deck'] = ['rank-5 diams']

        game_states['hands'] = [
            ['rank-2 diams'  , 'rank-2 spades'], 
            ['rank-3 diams'  , 'rank-3 spades', 'rank-3 clubs'], 
            ['rank-4 diams'  , 'rank-4 spades', 'rank-4 clubs', 'rank-4 hearts']
        ]
        go_fish(2)
        self.assertTrue('rank-5 diams' in game_states['hands'][2])
        self.assertEqual(game_states['deck'], [])
        self.assertFalse(go_fish(2))
        
    # Reads game_states['num_of_players'] and player_states['state_of_game']
    def test_ready_to_play():
        global game_states, player_states
        game_states['num_of_players'] = 3
        player_states['state_of_game'] = []
    
    # Calls ready_to_play()
    # Reads game_states['in_game']
    # Writes game_states['deck', 'hands', 'in_game']
    def test_start_game():
        pass
    
    # Reads game_states['hands']
    # Writes game_states['hands', 'matches']
    def test_matches(p_id, card_played):
        pass
    
    # Reads game_states['player', 'hands']
    # Writes game_states['hands']
    # Calls go_fish() matches()
    def test_lay_card(p_id, card_played, p_to_ask):
        pass
    

if __name__ == '__main__':
    unittest.main()