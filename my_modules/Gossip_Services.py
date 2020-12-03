# Message gossip


# Define a special message GossipMessage: Message with ttl
# Message gossip

# Message gossip
from p2psimpy import *
from p2psimpy.messages import BaseMessage
from p2psimpy.services.base import BaseHandler
from p2psimpy.storage import Storage


class GossipMessage(BaseMessage):
    __slots__ = ('sender', 'data')
    size = 1024

    def __init__(self, sender, data):
        super().__init__(sender, data)


class RequestUpdateMessage(BaseMessage):
    __slots__ = ('sender', 'data')

    def __init__(self, sender, index):
        super().__init__(sender, index)


class PullGossipService(BaseHandler, BaseRunner):

    def __init__(self, peer, init_timeout=200, fanout=20, request_update_interval=75, exclude_peers: set = None,
                 exclude_types: set = None):
        super().__init__(peer)

        self.init_timeout = init_timeout
        self.fanout = fanout
        self.request_update_interval = request_update_interval
        self.counter = 1

        if exclude_peers is None:
            self.exclude_peers = set()
        else:
            self.exclude_peers = exclude_peers
        self.exclude_types = exclude_types

        self.strg_name = 'msg_time'
        self.peer.add_storage(self.strg_name, Storage())
        self.last_known_index = 0
        self.largest_received_index = 0

    def handle_message(self, msg):
        if isinstance(msg, GossipMessage):
            self.handle_gossip_message(msg)
        if isinstance(msg, RequestUpdateMessage):
            self.handle_request_update_message(msg)

    def handle_gossip_message(self, msg):
        # Store message localy
        msg_id = msg.data
        idx = int(msg_id.split("_")[0])
        if idx > self.largest_received_index:
            self.largest_received_index = idx
        # Store the message id received with the current timestamp
        self.peer.store(self.strg_name, msg_id, self.peer.env.now)

    def handle_request_update_message(self, msg):
        request_index = msg.data
        if request_index < self.largest_received_index:
            receiver = msg.sender
            for i in range(request_index + 1, self.largest_received_index + 1):
                msg_data = self.peer.storage[self.strg_name].get_all_by_prefix(str(i) + "_")
                if len(msg_data) > 0:
                    self.peer.send(receiver, GossipMessage(self.peer, list(msg_data.keys())[0]))

    @property
    def messages(self):
        return GossipMessage, RequestUpdateMessage,

    def request_updates(self):
        for i in range(self.last_known_index + 1, self.largest_received_index + 2):
            msg_data = self.peer.storage[self.strg_name].get_all_by_prefix(str(i) + "_")
            if len(msg_data) == 0:
                self.last_known_index = i - 1
                break
        self.peer.gossip(RequestUpdateMessage(self.peer, self.last_known_index),
                         self.fanout, except_peers=self.exclude_peers, except_type=self.exclude_types)

    def run(self):
        # Wait the initial timeout
        yield self.env.timeout(self.init_timeout)
        while True:
            self.request_updates()
            yield self.env.timeout(self.request_update_interval)


from p2psimpy.services.base import BaseRunner


class MessageProducer(BaseRunner):

    def __init__(self, peer, init_timeout=1000, msg_rate=5, init_ttl=3, init_fanout=10):
        '''
        init_timeout: milliseconds to wait before starting the message production.
        msg_rate: number of messages per second
        init_ttl: ttl to set up for the message
        init_fanout: to how many peer send the message to
        '''
        super().__init__(peer)

        # calculate tx_interval
        self.init_timeout = init_timeout
        self.init_ttl = init_ttl
        self.init_fanout = init_fanout

        self.tx_interval = 1000 / msg_rate
        self.counter = 1

        # Let's add a storage layer to store messages
        self.strg_name = 'msg_time'
        self.peer.add_storage(self.strg_name, Storage())

    def produce_transaction(self):
        # Create a gossip message: message counter, peer_id and gossip it
        self.peer.gossip(GossipMessage(self.peer,
                                       '_'.join((str(self.counter), str(self.peer.peer_id)))),
                         self.init_fanout)
        # Locally store the message counter
        self.peer.store(self.strg_name, str(self.counter), self.peer.env.now)
        self.counter += 1

    def run(self):
        # Wait the initial timeout
        yield self.env.timeout(self.init_timeout)
        while True:
            self.produce_transaction()
            yield self.env.timeout(self.tx_interval)
