class BaseService(object):
    def __init__(self, peer, config):
        self.peer = peer
        self.config = config

    @property
    def env(self):
        return self.peer.env

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.peer.config.name)


class BaseHandler(BaseService):
    """
    BaseService that will trigger on a event handle_message
    """

    def handle_message(self, msg):
        """this callable is added as a listener to Peer.listeners"""
        raise NotImplementedError

    @property
    def messages(self):
        # Specify what messages will be processed by the service
        raise NotImplementedError


class BaseRunner(BaseService):

    def start(self):
        """Start service run"""
        self.env.process(self.run())

    def run(self):
        """The main running function"""
        raise NotImplementedError


class MockHandler(BaseHandler):
    """
    BaseService that will trigger on a event handle_message
    """

    def handle_message(self, msg):
        """this callable is added as a listener to Peer.listeners"""
        pass

    @property
    def messages(self):
        # Specify what messages will be processed by the service
        return self.config.messages


class MockRunner(BaseRunner):

    def start(self):
        """Start service run"""
        pass

    def run(self):
        """The main running function"""
        pass
