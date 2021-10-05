import asyncio
import gevent.pywsgi
import geventwebsocket.handler
import geventwebsocket
import bottle

app = bottle.Bottle()

async def socket_task(ws):
    counter = 0
    while True:
        message = ws.receive() # BLOCKING CALL
        if message is not None:
            if ( message == "Test" ):
                counter += 1
            ws.send(str(counter))

@app.route('/websocket')
def handle_websocket():
    wsock = bottle.request.environ.get('wsgi.websocket')
    if not wsock:
        bottle.abort(400, 'Expected WebSocket request.')
    asyncio.run(socket_task(wsock))
    
if __name__ == '__main__':
    server = gevent.pywsgi.WSGIServer(
        ("localhost", 8080), app, handler_class=geventwebsocket.handler.WebSocketHandler)
    server.serve_forever()
