from concurrency import *
from channel_init import *

# Create a channel with a capacity of 2
chan = make()

# Define a callback to handle the received value
def receiver(value, ok):
    if ok:
        print(f"Received: {value}")
    else:
        print("Channel closed, no value received.")

# Define a callback for when sending is complete
def sender_done():
    print("Value sent successfully.")

# Sending values into the channel
go(lambda: send(chan, 42, sender_done))
go(lambda: send(chan, 99, sender_done))
go(lambda: send(chan, 88, sender_done))
go(lambda: send(chan, 12, sender_done))
go(lambda: send(chan, 17, sender_done))

# Even thought the channel is closed, it sends from the buffer 
select()
# Run the event loop
run()

