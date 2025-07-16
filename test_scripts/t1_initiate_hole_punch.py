from utils.connection import Connection

c1 = Connection()
c1.initiate_hole_punch("127.0.0.2", 5000, 6000)
