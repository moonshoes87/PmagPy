#!/usr/bin/env python
def print_kwargs(**kwargs):
    """
    prints keyworded argument list
    """
    for key in kwargs:
        print '%s  %s' %(key, kwargs[key])
     
print_kwargs(arg1='one',arg2=42,arg3='ocelot')
