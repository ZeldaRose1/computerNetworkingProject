from utils.connection import Peer
from utils.menu import PeerMenu

p1 = Peer()
p1.name = "Client 1"

p1.connect_to_server("10.0.0.100", 7000)
PeerMenu(p1).run()