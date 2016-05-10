"""
A slight extension of pyAIML's Kernel class, to allow parsing of AIML tags
contained in a buffer, as well as a simplified plain-text-like format to ease
writing AIML rules.
"""

import sys
import logging
import re
import unicodedata
from functools import partial

from xml.sax import parseString, SAXParseException
from aiml import Kernel
from aiml.AimlParser import AimlHandler

from .utils import KrnlException


LOG = logging.getLogger( __name__ )



def normalize_string(input_str):
    """
    Normalize a string, removing diacritical characters (mapping
    them to the closest equivalent char).
    """
    # http://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string
    # http://stackoverflow.com/questions/4162603/python-and-character-normalization
    nkfd_form = unicodedata.normalize('NFKD', unicode(input_str))
    return nkfd_form.encode('iso8859-1','ignore')
    #return u"".join( [c for c in nkfd_form if not unicodedata.combining(c)] )



def split_rules( lines ):
    """
    Take a list of lines and group them by bunches separated with blank lines
    """
    rule = []
    for l in lines:
        if l:
            rule.append( l )
        elif rule:
            yield rule
            rule = []
    if rule:
        yield rule


def srai_sub( repl, g ):
    """Version of <srai> cleaning with punctuation removal"""
    return '<srai>' + re.sub( repl, ' ', g.group(1) ).upper() + '</srai>'

def srai_plain( g ):
    """Version of <srai> cleaning without punctuation removal"""
    return '<srai>' + g.group(1).upper() + '</srai>'


def build_aiml( lines, re_clean=None ):
    """
    Build a proper AIML buffer out of rules written with a simplified syntax.
    Each rule is writen as simple text lines

       PATTERN
       TEMPLATE

    or

       PATTERN
       <that>PATTERN-SIDE-THAT
       TEMPLATE

    where TEMPLATE is arbitrary code, including AIML tags, and can span
    more than one line. Patterns and <srai> fields are automatically converted 
    to uppercase and removed of punctuation.

    Rules are separated by blank lines. Lines starting with \c # are comments.
    """
    #print u"TEXT INPUT:  ", lines
    aiml = u'<?xml version="1.0" encoding="utf-8"?><aiml version="1.0">'
    fsrai = partial( srai_sub, re_clean ) if re_clean else srai_plain
    for rule in split_rules(lines):
        if len(rule)<2:
            raise RuntimeException(u'invalid rule:\n' + u'\n'.join(rule) )
        # Clean the pattern 
        pattern = re.sub( re_clean, ' ', rule[0] ) if re_clean else rule[0]
        aiml += u'<category><pattern>{}</pattern>'.format( pattern.upper() )
        # See if the 2nd line is a pattern-side that
        if rule[1].startswith('<that>'):
            aiml += rule[1]
            if not rule[1].endswith('</that>'):
                aiml += '</that>'
            rule = rule[1:]
        # Compile the template, including cleaning up <srai> elements
        tpl = u'\n'.join( rule[1:] )
        tpl = re.sub( '<srai>(.+)</srai>', fsrai, tpl )
        aiml += u'<template>{}</template></category>'.format(tpl)
    aiml += u'</aiml>'
    #print u"AIML OUTPUT: ", aiml.encode('utf-8')
    return aiml


# -------------------------------------------------------------------------

class AimlBot( Kernel, object ):
    """
    A subclass of the standard AIML kernel, with the added functionality
    of being able to slurp a string buffer containing AIML statements
    """

    def __init__( self, *args, **kwargs ):
        # Start parent
        super( AimlBot, self ).__init__()
        # Charset encoding we will always deliver to the AIML kernel
        self._enc = 'utf-8'
        self.setTextEncoding( self._enc )
        # Bot name
        if 'name' in kwargs:
            self.setPredicate( 'name', kwargs['name'] )
        # Same as self._brain._puncStripRE, but taking out * and _
        punctuation = "\"`~!@#$%^&()-=+[{]}\|;:',<.>/?"
        self._patclean = re.compile("[" + re.escape(punctuation) + "]")


    def learn_buffer( self, lines, fmt='aiml', clean_pattern=True ):
        """
        Learn the AIML stored in a buffer
         @param lines (list): a list of text lines
         @param fmt (str): buffer format: \c aiml or \c text
         @param clean_pattern (bool): for text format, if pattern & <srai>
           fields are to be sanitized
        """
        # Prepare the buffer. If it's not native AIML, it will contain rules
        # in simplified text; process them
        if fmt == 'aiml':
            buffer = u'\n'.join(lines).encode( self._enc )
        else:
            p = self._patclean if clean_pattern else None
            buffer = build_aiml( lines, p ).encode( self._enc )

        # Create a handler
        handler = AimlHandler( self._enc )
        handler.setEncoding( self._textEncoding )

        # Parse the XML buffer with that handler
        try: 
            parseString(buffer,handler)
        except SAXParseException as e:
            # Find where the parser broke
            lines = buffer.split('\n')
            row = e.getLineNumber()
            col = e.getColumnNumber()
            start = col-10 if col>10 else 0
            buf = lines[row-1][start:start+20]
            if start > 0:
                buf = '...' + buf
            if start+20 < len(lines[row-1]):
                buf += '...'
            LOG.warn( '%s : %s', e,  buf )
            msg = '{}: row={} col={}:\n{!s}', e.getMessage(), row, col, buf
            raise KrnlException( *msg )

        # Store the pattern/template pairs in the PatternMgr
        for key,tem in handler.categories.items():
            self._brain.add(key,tem)
        #self._brain.dump()


