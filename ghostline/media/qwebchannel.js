/**
 * QWebChannel JavaScript library
 * Based on Qt's implementation for communication between web pages and Qt C++
 */

(function() {
    if (typeof QWebChannel !== 'undefined') {
        return; // Already loaded
    }

    function QWebChannel(transport, initCallback) {
        if (typeof transport !== 'object') {
            console.error('[QWebChannel] Invalid transport object');
            return;
        }

        this.transport = transport;
        this.send = function(data) {
            if (typeof data !== 'string') {
                data = JSON.stringify(data);
            }
            this.transport.send(data);
        };

        this.onmessage = function(data) {
            try {
                var message = typeof data === 'string' ? JSON.parse(data) : data;
                this.handleMessage(message);
            } catch (e) {
                console.error('[QWebChannel] Error parsing message:', e);
            }
        };

        this.objects = {};
        this.callbacks = {};
        this.nextId = 1;

        var self = this;

        this.transport.onmessage = function(event) {
            self.onmessage(event.data);
        };

        this.handleMessage = function(message) {
            var response;

            if (message.type === 'response') {
                if (typeof this.callbacks[message.id] === 'function') {
                    this.callbacks[message.id](message.data);
                }
                delete this.callbacks[message.id];
            } else if (message.type === 'propertyUpdate') {
                for (var i in message.data) {
                    var obj = this.objects[message.object];
                    if (obj) {
                        obj[message.property] = message.data[i];
                    }
                }
            } else if (message.type === 'signal') {
                var obj = this.objects[message.object];
                if (obj) {
                    obj[message.signal].apply(obj, message.args);
                }
            } else if (message.type === 'init') {
                for (var name in message.objects) {
                    this.initObject(name, message.objects[name], message.data[name]);
                }
                if (initCallback) {
                    initCallback(this);
                }
            }
        };

        this.initObject = function(name, methods, data) {
            var obj = {};
            for (var method in methods) {
                obj[method] = (function(m) {
                    return function() {
                        var args = [];
                        for (var i = 0; i < arguments.length; ++i) {
                            if (typeof arguments[i] === 'function') {
                                var id = self.nextId++;
                                self.callbacks[id] = arguments[i];
                                args.push({__callback__: id});
                            } else {
                                args.push(arguments[i]);
                            }
                        }
                        self.send({
                            type: 'method',
                            object: name,
                            method: m,
                            args: args
                        });
                    };
                })(method);
            }

            for (var prop in data) {
                obj[prop] = data[prop];
            }

            this.objects[name] = obj;
        };

        // Request initialization
        this.send({type: 'init'});
    }

    console.log('[GHOSTLINE-DEBUG-INSIDE-IIFE] About to set window.QWebChannel, typeof QWebChannel =', typeof QWebChannel);
    window.QWebChannel = QWebChannel;
    console.log('[GHOSTLINE-DEBUG-INSIDE-IIFE] Set window.QWebChannel =', typeof window.QWebChannel);
})();
