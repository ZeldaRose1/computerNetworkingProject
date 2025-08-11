from utils.connection import Rendezvous

# Instantiate Rendezvous object
r = Rendezvous()

# Start server
r.listen("10.0.0.100", 7000)
