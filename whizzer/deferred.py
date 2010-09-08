import logging

class AlreadyCalledError(Exception):
    """Error signifying the deferred has already been called."""

class Deferred(object):
    """A generalized callback framework used for handling future results.
    
    Ex:

    Chaining:
    d = Deferred()
    d.add_callback(print).add_callback(log).add_callback(close)

    d.callbacks("Hello") # print is called with the result, log is called with the result of print, close is called with the result of log

    Branching:
    d = Deferred()
    d.add_callback(log)
    d.add_callback(close)
    d.callbacks("Hello") # print is called with the result, log is called with the result
    
    Error handling:
    d = Deferred()
    d.add_errback(failme).add_callbacks(print, log)

    f.exception() # failme is called with the exception as its only parameter, if failme raises log is called, if not print is called

    """
    def __init__(self, logger=None):
        if logger:
            self.logger = logger
        else:
            logger = logging.getLogger('deferred')
            logger.addHandler(logging.StreamHandler())
            logger.setLevel(logging.DEBUG)

        self._called = False
        self._callbacks = []
        self._errbacks = []
   
    def callback(self, result):
        """Perform the callbacks added to this deferred."""
        if self._called:
            raise AlreadyCalledError()

        for (d, cb, cb_args, cb_kwargs) in self._callbacks:
            r = None
            e = None
            err = False
        
            try:
                r = cb(result, *cb_args, **cb_kwargs)
            except Exception as _e:
                e = _e
                err = True

            if err:
                d.errbacks(e)
            else:
                d.callbacks(r)
    
    def errback(self, result):
        """Perform the errbacks added to this deferred."""
        if self._called:
            raise AlreadyCalledError()

        for (d, cb, cb_args, cb_kwargs) in self._errbacks:
            r = None
            e = None
            err = False

            if cb:
                try:
                    r = cb(result, *cb_args, **cb_kwargs)
                except Exception as _e:
                    e = _e
                    err = True
                if err:
                    d.errbacks(e)
                else:
                    d.callbacks(r)
            else:
                self.logger.debug(str(e))

    def add_callback(self, callback, *args, **kwargs):
        """Add a callback and return a deferred."""
        if self._called:
            raise AlreadyCalledError()

        d = Deferred()
        self._callbacks.append((d, callback, args, kwargs))
        return d

    def add_errback(self, errback, *args):
        """Add a errback."""
        if self._called:
            raise AlreadyCalledError()

        d = Deferred()
        self._errbacks.append((d, errback, args))
        return d

    def add_callbacks(self, callback, errback, cb_args, cb_kwargs, eb_args, eb_kwargs):
        """Same as doing add_callback and add_errback but in one call."""
        if self._called:
            raise AlreadyCalledError()

        f = Future(self.future._loop)
        d = Deferred()
        self._callbacks.append((d, callback, cb_args, cb_kwargs))
        self._errbacks.append((d, errback, eb_args, eb_kwargs))
        return d

    def wait(self, loop):
        """Wait for this differed to be called."""
        while not self._called:
            loop.loop(pyev.EVLOOP_NONBLOCK)