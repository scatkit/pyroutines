from channel_init import *
from random import randint
import builtins

execution_queue = []

def go(callback):
    if callback:
        execution_queue.append(callback) 

def run():
    WaitingQueue.total = 0
    while execution_queue:
        f = execution_queue.pop(0)
        f()
    try:
        if WaitingQueue.total > 0:
            raise Exception("Fatal Error: all go routines are asleep! - deadlock")
    except Exception as e:
        print(e)
                

def make(capacity=0):
    return Channel(capacity)

def len(channel):
    return builtins.len(channel.buffer)

def cap(channel):
   return channel.capacity

def send(channel, value, callback):
    if not channel:
        WaitingQueue.total+=1
        return
    
    if channel.closed:
        raise Exception("send on a closed channel")
    
    # In case recv was called first
    if channel.waiting_to_recv:
        print(f"Length of the recv channel: {builtins.len(channel.waiting_to_recv)}")
        receiver = channel.waiting_to_recv.dequeue() # recv's callback
        print(f"Reciver: {receiver}")
        go(callback) # Running the send's callback before recv's
        go(lambda: receiver(value, True)) 
        return
        
    if len(channel) < cap(channel):
        channel.buffer.append(value)
        go(callback)
        return
    
    print(f"Enqueuing {(value,callback)} to the waiting channel")
    channel.waiting_to_send.enqueue(value)

def recv(channel, callback):
    # Receiving from nil channel blocks forever
    if not channel:
        print("Channel is nil")
        WaitingQueue.total+=1 
        return
    
    if len(channel) > 0:
        print("Sent from the buffer")
        value = channel.buffer.pop(0)
        print(value)
        go(lambda: callback(value, True)) 
        return
    
    # In case send is called first
    if channel.waiting_to_send: 
        print(f"Length of the wait channel: {builtins.len(channel.waiting_to_send)}")
        value, sender = channel.waiting_to_send.dequeue() 
        print(f"Value received: {value}. Sender: {sender}")
        go(lambda: callback(value, True))
        go(sender)
        return
        
    # A receiver on a closed channel can always proceed immediately,
    # yeilding the element type's zero value 
    if channel.closed:
        go(lambda: callback(None, False))
        return
        
    # If recv is called first, enqueue that and wait for sending channel
    print(f"Equeuing {callback} to recv channel queue")
    channel.waiting_to_recv.enqueue(callback)
    
def close(channel):
    if channel.closed:
        raise Exception("close of a closed channel")
    
    channel.closed = True
    
        # Complete any senders
    while channel.waiting_to_send:
        value, callback = channel.waiting_to_send.dequeue()
        send(channel, value, callback)
        
        # Complete any receivers
    while channel.waiting_to_recv:
        callback = channel.waiting_to_recv.dequeue()
        recv(channel, callback)
        


default = object()
def select(cases, callback=None):
    def is_ready(case): 
        if case[0] == send:
            return case[1].closed or len(case[1]) < cap(case[1]) or case[1].waiting_to_recv # if either true, returns true
        elif case[0] == recv:
            return case[1].closed or len(case[1]) > 0 or  case[1].waiting_to_send # if value are in the waiting_to_send queue or inside the buffer
        elif case[0] == default:
            return False
        
    '''
    Case structure: [recv, Channel, callback(value, ok)]
    '''
    ready_to_proceed = [case for case in cases if is_ready(case)]
    
    if ready_to_proceed:
        case = ready_to_proceed[randint(0,builtins.len(ready_to_proceed)-1)] #send or recv
        if case[0] == send:
            send(case[1],case[2],case[3]) #channel, value, callback
        elif case[0] == recv: 
            recv(case[1],case[2]) #channel, callback
        go(callback)
        return
    
    defaults = [case for case in cases if case[0] == default]
    
    if defaults:
        defaults[0]() 
        go(callback)
        return
    
    wrapped = []
    
    def cleanup():
        for case in wrapped:
            if case[0] == send:
                case[1].waiting_to_send.dequeue((case[2], case[3])) # case[1] is channel, case[2] is val, case[3] is callback
            elif case[0] == recv:
                case[1].wating_to_recv.dequeue(case[2])
        go(callback)
    
    for case in cases:
        if case[0] == send:
            new_case = (case[0],case[1],case[2], lambda: (cleanup(), case[3]())) 
            case[1].waiting_to_send.enqueue((new_case[2], case[3])) # value, callback
            wrapped.append(new_case)
            
        elif case[0] == recv:
            new_case = (case[0], case[1], lambda value, ok: (cleanup(), case[2](value, ok)))
            case[1].waiting_to_recv.enqueue(new_case[2])
            wrapped.append(new_case)
            
