from utils.connection import Connection

c2 = Connection()

# Please note that this is binding to source port 5000
# The listening port will be port 6000, and sending to 6000
c2.initiate_hole_punch("127.0.0.2", 6000, 5000)

while True:
    a = input("Please type message to send:\n")
    c2.active_socket.send(bytes(a))

