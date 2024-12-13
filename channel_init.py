class Channel:
    def __init__(self,capacity):
        self.capacity = capacity
        self.buffer = []
        self.closed = False
        self.waiting_to_send = WaitingQueue()
        self.waiting_to_recv= WaitingQueue()
        
class WaitingQueue(list):
    total = 0
    
    def show(self):
        return self
    
    def enqueue(self, x):
        WaitingQueue.total+=1
        self.append(x)
     
    def dequeue(self, x=None):
        if x == None:
            x = self.pop(0)
            WaitingQueue.total -=1
        else:
            idx = self.index(x)
            if idx: 
                self.pop(idx)
                WaitingQueue.total-=1
        return x


