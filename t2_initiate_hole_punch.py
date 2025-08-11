from utils.connection import Peer
from utils.menu import PeerMenu

p2 = Peer()
p2.name = "Client 2"

p2.connect_to_server("10.0.0.100", 7000)
PeerMenu(p2).run()