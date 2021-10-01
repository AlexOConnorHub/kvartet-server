import threading
import flask
import flask_sockets
import random
import _thread


class kvarteto:
    def __init__(self):
        self.num_of_players = 0
        self.started_game = False
        self.player_turn = 0

    def add_player(self):
        if (not self.started_game):
            self.num_of_players += 1
            return True
        return False

    def start_game(self):
        if (not self.started_game):
            self.started_game = True
            self.player_turn = random.randrange(1, (self.num_of_players + 1))
            return True
        return False


app = flask.Flask(__name__)
sockets = flask_sockets.Sockets(app)
kavarteto_game = kvarteto()


def socket_thread():
    pass


@sockets.route('/kvarteto')
def echo_socket(ws):
    kavarteto_game.add_player()
    while not ws.closed:
        start_new_thread(socket_thread, (c,))
        message = ws.receive()
        print(message)
        ws.send(message)


if __name__ == '__main__':
    app.run(use_debugger=False, use_reloader=False, passthrough_errors=True)
