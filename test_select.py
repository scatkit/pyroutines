from channel_init import *
from concurrency import *

def copy(getway: Channel, ch: Channel):
    def onrecv(val, ok):
        if ok:
            send(getway, val, lambda: copy(getway, ch))
        else:
            close(getway)
    recv(ch, onrecv)
    
def sendall(ch: Channel, arr: list):
    if arr:
        send(ch, arr[0], lambda: sendall(ch, arr[1:])) 
    else:
        close(ch)


def recvall(ch: Channel, callback):
    vals = []
    
    def onrecv(val, ok):
        if ok:
            vals.append(val)
            recv(ch, onrecv) # If the loop continues, make sure there is a recv channel reservei in the queue
        else:
            callback(vals)
    recv(ch, onrecv)
    
            
def slct(getway: Channel, ch1: Channel, ch2: Channel):
    def first_channel(value, ok):
        if ok:
            send(getway, value, lambda: slct(getway, ch1, ch2))
        else: # In case first channel is closed, recv a value from the second channel
            copy(getway, ch2)

    def second_channel(value, ok): 
        if ok:
            send(getway, value, lambda: slct(getway, ch1, ch2))
        else: 
            copy(getway, ch1)

    select([
        (recv, ch1, first_channel),
        (recv, ch2, second_channel),
        ])
    

def test_select():
    def callback(result):
        print(result)
        assert [x for x in sorted(result)] == [0,2,4]
                
    ch1, ch2, ch3 = make(5), make(5), make(5) 
    go(lambda: sendall(ch2, [4,2])) 
    go(lambda: sendall(ch3, [0])) 
    go(lambda: slct(ch1,ch2,ch3))
    go(lambda: recvall(ch1, callback))
    run()
    
test_select()


