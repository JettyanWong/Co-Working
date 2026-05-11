from flask import request
from flask_socketio import emit, join_room, leave_room
from app import socketio, db
from y_py import YDoc
from app.models import Document as DocModel
import time

# In-memory Yjs document store
doc_states = {}  # { doc_id: {'ydoc': YDoc, 'last_persist': timestamp} }


def get_or_create_ydoc(doc_id):
    """Load YDoc from DB or create new one."""
    if doc_id not in doc_states:
        ydoc = YDoc()
        # Load stored state from DB if available
        doc = DocModel.query.get(int(doc_id))
        if doc and doc.content:
            try:
                ydoc.apply_update(bytes(doc.content))
            except Exception:
                pass
        doc_states[doc_id] = {'ydoc': ydoc, 'last_persist': time.time()}
    return doc_states[doc_id]['ydoc']


def persist_ydoc(doc_id):
    """Persist YDoc state to database."""
    if doc_id not in doc_states:
        return
    ydoc = doc_states[doc_id]['ydoc']
    state = ydoc.encode_state_as_update()
    doc = DocModel.query.get(int(doc_id))
    if doc:
        doc.content = bytes(state)
        db.session.commit()
        doc_states[doc_id]['last_persist'] = time.time()


@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")


@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")


@socketio.on('join_doc')
def handle_join_doc(data):
    doc_id = data.get('doc_id')
    user_id = data.get('user_id', 'anonymous')
    if not doc_id:
        return

    join_room(doc_id)
    print(f"User {user_id} joined doc {doc_id}")

    # Send full Yjs state to the joining client
    try:
        client_ydoc = YDoc()
        server_ydoc = get_or_create_ydoc(doc_id)
        state = server_ydoc.encode_state_as_update()
        emit('yjs_init', {'doc_id': doc_id, 'state': list(bytes(state))}, room=request.sid)
    except Exception as e:
        print(f"Error sending init state: {e}")

    # Notify others
    emit('user_joined', {'user_id': user_id, 'sid': request.sid}, room=doc_id, include_self=False)


@socketio.on('leave_doc')
def handle_leave_doc(data):
    doc_id = data.get('doc_id')
    user_id = data.get('user_id', 'anonymous')
    if not doc_id:
        return

    leave_room(doc_id)
    emit('user_left', {'user_id': user_id, 'sid': request.sid}, room=doc_id, include_self=False)


@socketio.on('yjs_sync')
def handle_yjs_sync(data):
    """Apply Yjs update to server state and broadcast to other clients."""
    doc_id = data.get('doc_id')
    update = data.get('update')
    if not doc_id or not update:
        return

    try:
        ydoc = get_or_create_ydoc(doc_id)
        ydoc.apply_update(bytes(update))
    except Exception as e:
        print(f"Error applying update: {e}")

    # Broadcast to other clients
    emit('yjs_sync', {'doc_id': doc_id, 'update': update}, room=doc_id, include_self=False)


@socketio.on('cell_add')
def handle_cell_add(data):
    doc_id = data.get('doc_id')
    if not doc_id:
        return
    emit('cell_add', data, room=doc_id, include_self=False)


@socketio.on('cell_delete')
def handle_cell_delete(data):
    doc_id = data.get('doc_id')
    if not doc_id:
        return
    emit('cell_delete', data, room=doc_id, include_self=False)


@socketio.on('cursor_update')
def handle_cursor_update(data):
    doc_id = data.get('doc_id')
    if not doc_id:
        return
    emit('cursor_update', {
        'doc_id': doc_id,
        'cell_id': data.get('cell_id'),
        'position': data.get('position'),
        'user_id': data.get('user_id', 'anonymous'),
        'username': data.get('username', 'Anonymous'),
        'sid': request.sid
    }, room=doc_id, include_self=False)
