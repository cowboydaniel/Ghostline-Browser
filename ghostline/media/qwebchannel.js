/**
 * Minimal QWebChannel implementation for local testing and fallback
 * This provides the QWebChannel class that the Qt WebEngine should provide via its resources.
 */
(function() {
    if (typeof QWebChannel !== 'undefined') {
        return; // Already loaded
    }

    window.QWebChannel = function(transport, initCallback) {
        this.transport = transport;
        this.objects = {};
        this.callbacks = {};
        this.pendingMessages = [];

        var self = this;

        // Listen for messages from the C++ side
        this.transport.onmessage = function(event) {
            try {
                var message = JSON.parse(event.data);
                if (message.type === 'response') {
                    if (self.callbacks[message.id]) {
                        self.callbacks[message.id](message.result);
                        delete self.callbacks[message.id];
                    }
                } else if (message.type === 'init') {
                    // Initialize objects
                    if (message.objects) {
                        for (var name in message.objects) {
                            self.initObject(name, message.objects[name]);
                        }
                    }
                    if (initCallback) {
                        initCallback(self);
                    }
                }
            } catch (e) {
                console.error('[QWebChannel] Error processing message:', e);
            }
        };

        // Request initialization
        this.transport.send(JSON.stringify({ init: true }));
    };

    QWebChannel.prototype.initObject = function(name, methods) {
        var self = this;
        this.objects[name] = {};

        for (var i = 0; i < methods.length; i++) {
            var method = methods[i];
            this.objects[name][method] = (function(methodName) {
                return function() {
                    var args = Array.prototype.slice.call(arguments);
                    var callback = null;
                    if (args.length > 0 && typeof args[args.length - 1] === 'function') {
                        callback = args.pop();
                    }

                    var id = Math.random().toString(36);
                    if (callback) {
                        self.callbacks[id] = callback;
                    }

                    self.transport.send(JSON.stringify({
                        id: id,
                        object: name,
                        method: methodName,
                        args: args
                    }));
                };
            })(method);
        }
    };
})();
