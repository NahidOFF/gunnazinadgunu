#!/usr/bin/env python3
"""The date reading (red = month, blue = day) was the standing rival to the letter-index
reading, and the notes recorded it as neither confirmable nor refutable.  It does make
one check nobody ran: days of the month spread over 1..31, and these do not."""
import math
red =[6,2,6,9,6,4,10,5,8,7,7,2,7,7]
blue=[5,4,6,5,8,8,14,7,9,   4,11,9,1]      # thirteen known; piece 15's blue is unread
def z(vals, mu, var): return (sum(vals)/len(vals)-mu)/math.sqrt(var/len(vals))
print('red  n=%d mean %.2f max %d'%(len(red),sum(red)/len(red),max(red)))
print('blue n=%d mean %.2f max %d'%(len(blue),sum(blue)/len(blue),max(blue)))
print('\nblue as day-of-month, uniform 1..31:')
print('  P(all <= 14) = %.3g'%((14/31)**len(blue)))
print('  z(mean) = %.2f'%z(blue,16.0,(31*31-1)/12))
print('\nred as month, uniform 1..12:  z(mean) = %.2f'%z(red,6.5,(144-1)/12))
print('\nboth as a letter index into a name of length L:')
for L in (9,11,13,15):
    print('  L=%2d  z(red) %+.2f  z(blue) %+.2f'%(L,z(red,(L+1)/2,(L*L-1)/12),z(blue,(L+1)/2,(L*L-1)/12)))
