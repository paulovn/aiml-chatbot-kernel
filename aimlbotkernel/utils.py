"""
Miscellaneous utility functions
"""
from __future__ import absolute_import, division, print_function

import logging

# A logger for this file
LOG = logging.getLogger( __name__ )

# Default wrapping class for an output message
HTML_DIV_CLASS = 'krn-bot'


# ----------------------------------------------------------------

def is_collection(v):
    """
    Decide if a variable contains multiple values and therefore can be
    iterated, discarding strings (single strings can also be iterated, but
    shouldn't qualify)
    """
    # The 2nd clause is superfluous in Python 2, but (maybe) not in Python 3
    # Therefore we use 'str' instead of 'basestring'
    return hasattr(v,'__iter__') and not isinstance(v,str)



# ----------------------------------------------------------------------

def escape( x, lb=False ):
    """
    Ensure a string does not contain HTML-reserved characters (including
    double quotes)
    Optionally also insert a linebreak if the string is too long
    """
    # Insert a linebreak? Roughly around the middle of the string,
    if lb:
        l = len(x)
        if l >= 10:
            l >>= 1                     # middle of the string
            s1 = x.find( ' ', l )       # first ws to the right
            s2 = x.rfind( ' ', 0, l )   # first ws to the left
            if s2 > 0:
                s = s2 if s1<0 or l-s1 > s2-l else s1
                x = x[:s] + '\\n' + x[s+1:]
            elif s1 > 0:
                x = x[:s1] + '\\n' + x[s1+1:]
    # Escape HTML reserved characters
    return x.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# ----------------------------------------------------------------------

def div( txt, *args, **kwargs ):
    """
    Create & return an HTML <div> element by wrapping the passed text buffer.
      @param txt (basestring): the text buffer to use
      @param *args (list): if present, \c txt is considered a Python format
        string, and the arguments are formatted into it
      @param kwargs (dict): the \c css field can contain the CSS class for the
        <div> element
    """
    if args:
        txt = txt.format( *args )
    css = kwargs.get('css',HTML_DIV_CLASS)
    out = u'<div class="{}">{}</div>'.format( css, txt )
    return u'<div class="{}">{}</div>'.format( css, txt )


def data_msglist( msglist ):
    """
    Return a Jupyter display_data message, in both HTML & text formats, by 
    joining together all passed messages.
      @param msglist (iterable): an iterable containing a list of tuples
        (message, css_style)

    Each message is either a text string, or a list. In that case it is
    assumed to be a format string + parameters.
    """
    txt = html = u''
    LOG.debug( "msglist: %r", msglist )
    for msg, css in msglist:
        if is_collection(msg):
            msg = msg[0].format(*msg[1:])
        html += div( escape(msg).replace('\n','<br/>'), css=css or 'msg' )
        txt += msg + "\n"
    return { 'data': {'text/html' : div(html),
                      'text/plain' : msg },
             'metadata' : {} }


def data_msg( msg, mtype=None ):
    """
    Return a Jupyter display_data message, in both HTML & text formats, by 
    formatting a given single message.
      @param msg (str,list): a string, or a list of format string + args
      @param mstype (str): the message type (used for the CSS class)
    """
    if isinstance(msg,KrnlException):
        return msg() # a KrnlException knows how to format itself
    else:
        return data_msglist( [ (msg, mtype) ] )



# ----------------------------------------------------------------------

class KrnlException( Exception ):
    """
    An exception for kernel errors. Will generate a Jupyter message
    to be sent to the frontend
    """
    def __init__(self, msg, *args):
        if isinstance(msg,Exception):
            msg = repr( msg )
        elif len(msg):
            msg = msg.format(*args)
        LOG.warn( "KrnlException: %s", msg, exc_info=1 )
        super(KrnlException,self).__init__(msg)

    def __call__(self):
        """
        When called as a function, it generates a Jupyter display data message
        """
        msg = escape(self.args[0]).replace('\n','<br/>')
        html = div( div(u'<span class="title">Error:</span> '+msg, css="error") )
        return { 'data': {'text/html' : html,
                          'text/plain' : 'Error: ' + self.args[0] },
                 'metadata' : {} }



