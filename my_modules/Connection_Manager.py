from p2psimpy.services.connection_manager import  *


class ClientP2PConnectionManager(P2PConnectionManager):

    def recv_hello(self, msg):
        """
        Receive introduction message
        """
        other = msg.sender
        if other not in self.peer.connections and len(self.connected_peers) < self.max_peers:
            self.peer.connect(other)
            self.peer.send(other, Hello(self.peer))
            self.peer.send(other, RequestPeers(self.peer))