from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def test_connect():
    print('Client connected')

@socketio.on('join')
def join(message):
    print('joined room: ' + message['room'])
    join_room(message['room'])

@socketio.on('room_send')
def send_room_message(message):
    print(message)
    emit('from_server', message['message'], room=message['room'])

@socketio.on('leave', namespace='/test')
def leave(message):
    leave_room(message['room'])

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, host = '0.0.0.0', port = 8001)
