from channel_init import *
from random import randint
import builtins
import asyncio

execution_queue = []

def go(task):
    if task:
        asyncio.create_task(task) # execution queue provided by asyn


def make(capacity=0):
    return Channel(capacity)

def len_buf(channel):
    return builtins.len(channel.buffer)

def cap(channel):
   return channel.capacity

async def send(channel, value): 
    if not channel:
        await asyncio.Future() 
        
    if channel.closed:
        raise Exception("send on a closed channel")
    
    if channel.waiting_to_recv:
        future = channel.waiting_to_recv.dequeue() # receives the box
        future.set_result((value, True)) # put data into the box
        return
        
    if len_buf(channel) < cap(channel):
        channel.buffer.append(value)
        return
    
    future = asyncio.Future()
    channel.waiting_to_send.enqueue((value, future)) # save the data
    await future # waiting for the box

async def recv(channel):
    if not channel:
        await asyncio.Future()
    
    if len_buf(channel) > 0:
        value = channel.buffer.pop(0)
        return value, True
    
    # in case there are still some values in WQS
    if channel.waiting_to_send: 
        value, future = channel.waiting_to_send.dequeue() # data, box
        future.set_result(None) 
        return value, True
        
    if channel.closed:
        return None, False
        
    future = asyncio.Future()
    channel.waiting_to_recv.enqueue(future) # sends the box
    value, ok = await future # waits for WQS to put data in and return it
    return value, ok


default = object() 
 
async def select(cases):
    
    # Block forever
    if builtins.len(cases) == 0:
        await asyncio.Future()
    
    def is_ready(case): 
        if case[0] == send:
            return case[1].closed or len_buf(case[1]) < cap(case[1]) or case[1].waiting_to_recv # if either true, returns true
        elif case[0] == recv:
            return case[1].closed or len_buf(case[1]) > 0 or case[1].waiting_to_send # if value are in the waiting_to_send queue or inside the buffer
        elif case[0] == default:
            return False
        
    ready_to_proceed = [case for case in cases if is_ready(case)]
    
    if ready_to_proceed:
        case = ready_to_proceed[randint(0,builtins.len(ready_to_proceed)-1)] #send or recv
        if case[0] == send:
            await send(case[1],case[2]) #channel, value, callback
            await case[3]()
        elif case[0] == recv: 
            value, ok = await recv(case[1]) #channel, callback
            await case[2](value, ok)
        return
    
    defaults = [case for case in cases if case[0] == default]
    
    if defaults:
        await defaults[0]() 
        return
    
    futures = []
    
    for case in cases:
        future = asyncio.Future()
        if case[0] == send:
            case[1].waiting_to_send.enqueue((case[2], future))
        elif case[0] == recv:
            case[1].waiting_to_recv.enqueue(future)
        
    # as some futures get done, they get appended to the futures array
    done, _ =  asyncio.wait(futures, return_when = asyncio.FIRST_COMPLETE)
    
    for i, future in enumerate(futures):
        if future == done[0]:
            if cases[i][0] == send:
                await future 
                await case[3]() 
            elif case[i][0] == recv:
                value, ok = await future # waiting to receive a value
                await case[i][2](value, ok) #sending it back

