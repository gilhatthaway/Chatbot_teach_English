import time
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import socketio

SERVER = 'http://127.0.0.1:5000'


def make_client(user_id, listen_for_private=True):
    sio = socketio.Client()

    @sio.event
    def connect():
        print(f'[user{user_id}] connected')

    @sio.event
    def disconnect():
        print(f'[user{user_id}] disconnected')

    @sio.on('connected')
    def on_connected(data):
        print(f'[user{user_id}] server says:', data)

    @sio.on('message_error')
    def on_message_error(data):
        print(f'[user{user_id}] message_error:', data)

    if listen_for_private:
        @sio.on(f'private_message_{user_id}')
        def on_private(data):
            print(f'[user{user_id}] got private_message:', data)

    return sio


def run_test():
    a = make_client(1, listen_for_private=False)
    b = make_client(10, listen_for_private=True)

    a.connect(SERVER)
    b.connect(SERVER)

    time.sleep(1)

    print('Sending send_message event from user 1 -> user 10')
    a.emit('send_message', {'sender_id': 1, 'receiver_id': 10, 'content': 'SocketIO test message'})

    # wait to receive
    time.sleep(2)

    a.disconnect()
    b.disconnect()


if __name__ == '__main__':
    run_test()
