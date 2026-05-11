// Yjs CRDT collaborative editing over Flask-SocketIO

class YjsCollab {
    constructor(docId) {
        this.docId = docId;
        this.ydoc = null;
        this.socket = null;
        this.connected = false;
        this.changeHandlers = [];
    }

    connect() {
        this.socket = io();
        this.socket.on('connect', () => {
            this.connected = true;
            this.socket.emit('join_doc', { doc_id: this.docId });
        });
        this.socket.on('disconnect', () => {
            this.connected = false;
        });
    }

    init(initialState) {
        this.ydoc = new Y.Doc();
        if (initialState && initialState.length > 0) {
            Y.applyUpdate(this.ydoc, new Uint8Array(initialState));
        }

        const self = this;
        this.ydoc.on('update', (update) => {
            if (self.connected) {
                self.socket.emit('yjs_sync', {
                    doc_id: self.docId,
                    update: Array.from(update)
                });
            }
        });

        this.socket.on('yjs_sync', (data) => {
            if (data.doc_id === self.docId && self.ydoc) {
                Y.applyUpdate(self.ydoc, new Uint8Array(data.update));
            }
        });

        this.socket.on('yjs_init', (data) => {
            if (data.doc_id === self.docId && self.ydoc) {
                Y.applyUpdate(self.ydoc, new Uint8Array(data.state));
            }
        });
    }

    getYDoc() {
        return this.ydoc;
    }

    getState() {
        return this.ydoc ? Array.from(Y.encodeStateAsUpdate(this.ydoc)) : [];
    }

    disconnect() {
        if (this.socket) {
            this.socket.emit('leave_doc', { doc_id: this.docId });
            this.socket.disconnect();
        }
        if (this.ydoc) {
            this.ydoc.destroy();
            this.ydoc = null;
        }
    }
}

// Global registry
window.collabDocs = window.collabDocs || {};

function getOrCreateCollab(docId) {
    if (!window.collabDocs[docId]) {
        window.collabDocs[docId] = new YjsCollab(docId);
    }
    return window.collabDocs[docId];
}
