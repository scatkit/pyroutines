from concurrency import *
from channel_init import *
import asyncio

def merge(l, r):
    m = []
    while len(l) > 0 or len(r) > 0:
        if len(l) == 0:
            return m + r
        if len(r) == 0: 
            return m + l 
        if l[0] < r[0]:
            m.append(l[0])
            l = l[1:]
        else:
            m.append(r[0])
            r = r[1:]
    return m

async def merge_sort(arr):
    if builtins.len(arr) <= 1:
        return arr
    else:
        lc, rc = make(), make()
        
        async def left():
            value = await merge_sort(arr[:len(arr)//2])
            await send(lc, value) 
        go(left())
        
        async def right():
            value = await merge_sort(arr[len(arr)//2:])
            await send(rc, value)
        go(right())
        
        l_val, _ = await recv(lc)
        r_val, _ = await recv(rc)
        
        return merge(l_val, r_val)

def test_concurrent_merge_sort():
    async def main():
        result = await merge_sort([1,9,3,0,4])
        print(result)
        assert result == [0,1,3,4,9]
    asyncio.run(main())
    
test_concurrent_merge_sort()

