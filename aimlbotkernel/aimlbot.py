"""
A small extension of pyAIML's Kernel class, to add some modifications:
 * allow parsing of AIML documents contained in a buffer, 
 * allow also parsing a somehow simplified plain-text-like format (to ease 
   writing AIML rules)
 * allow iterating over predicates (either session or bot predicates).
 * load/save full bot states (not only brain, but also session & bot predicates)
 * improve date rendering by adding strftime() formatting, locale-dependent
 * set locale by defining the \c lang bot predicate
"""

from __future__ import absolute_import, division, print_function

import sys
import os.path
import logging
import re
import locale
import time
import unicodedata
import ConfigParser
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
    """Version of <srai> cleaning with uppercasing & punctuation removal"""
    return '<srai>' + re.sub( repl, ' ', g.group(1) ).upper() + '</srai>'

def srai_plain( g ):
    """Version of <srai> cleaning with uppercasing but without punctuation 
    removal"""
    return '<srai>' + g.group(1).upper() + '</srai>'


def build_aiml( lines, topic=None, re_clean=None, debug=False ):
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
    if debug: print( u"TEXT INPUT:  ", lines )
    aiml = u'' if topic is None else u'<topic name="{}">'.format(topic.upper())
    fsrai = partial( srai_sub, re_clean ) if re_clean else srai_plain
    for rule in split_rules(lines):
        if len(rule)<2:
            raise RuntimeException(u'invalid rule:\n' + u'\n'.join(rule) )
        # Clean the pattern 
        pattern = re.sub( re_clean, ' ', rule[0] ) if re_clean else rule[0]
        aiml += u'\n<category>\n<pattern>{}</pattern>'.format(pattern.upper())
        # See if the 2nd line is a pattern-side that
        if rule[1].startswith('<that>'):
            aiml += rule[1]
            if not rule[1].endswith('</that>'):
                aiml += '</that>'
            rule = rule[1:]
        # Compile the template, including cleaning up <srai> elements
        tpl = u'\n'.join( rule[1:] )
        tpl = re.sub( '<srai>(.+)</srai>', fsrai, tpl )
        aiml += u'\n<template>{}</template>\n</category>\n'.format(tpl)
    if topic is not None:
        aiml += u'\n</topic>'
    if debug: print( u"AIML OUTPUT: ", aiml.encode('utf-8') )
    return aiml


# -------------------------------------------------------------------------

class AimlBot( Kernel, object ):
    """
    A subclass of the standard AIML kernel, with some added functionality:
      * able to slurp a string buffer containing AIML statements
      * load/save full state to disk
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
        # A place to store the parsed AIML cells (TBD: save AIML to disk)
        self.aiml = None


    def learn_buffer( self, lines, fmt='aiml', opts={} ):
        """
        Learn the AIML stored in a buffer
         @param lines (list): a list of text lines
         @param fmt (str): buffer format: \c aiml or \c text
         @param opts (dict): options for text format:
             - topic (str): an optional \c <topic> wrapper
             - clean_pattern (bool): clean pattern & <srai> fields
        """
        # Prepare the buffer
        if fmt == 'aiml':
            # Native XML. Join lines, remove the preamble & <aiml> element
            buf = re.sub( r'''^ \s* (?:<\?xml[^>]+>)?
                                \s*<aiml[^>]*>
                                (.+)
                                </aiml>\s*$''',
                          r'\1', u'\n'.join(lines), flags=re.X|re.I|re.S )
        else:
            # Simplified text: process it
            clean = self._patclean if opts.get('clean_pattern') else None
            buf = build_aiml( lines, opts.get('topic'), clean )

        # Create a handler
        handler = AimlHandler( self._enc )
        handler.setEncoding( self._textEncoding )

        # Parse the XML buffer with that handler
        try: 
            # Do charset encoding & add the <aiml> XML wrapping
            xml = '<?xml version="1.0" encoding="utf-8"?>\n<aiml version="1.0">\n{}\n</aiml>'.format( buf.encode(self._enc) )
            parseString(xml,handler)
        except SAXParseException as e:
            # Find where the parser broke
            lines = xml.decode(self._enc).split('\n')
            #print( '\n'.join(lines) )
            row, col = e.getLineNumber(), e.getColumnNumber()
            start = col-25 if col>25 else 0
            errbuf = lines[row-1][start:start+50]
            below = '-' * (col-start) + '^'
            if start > 0:
                errbuf = u'...' + errbuf
                below = '---' + below
            if start+50 < len(lines[row-1]):
                errbuf += u'...'
            errbuf = errbuf + '\n' + below
            #LOG.warn( u'%s :\n%s', e,  errbuf )
            msg = u'{}: row={} col={}:\n{!s}', e.getMessage(), row, col, errbuf
            raise KrnlException( *msg )

        # Store the pattern/template pairs in the PatternMgr
        for key,tem in handler.categories.items():
            self._brain.add(key,tem)
        #self._brain.dump()
        # Add the processed AIML to the aiml buffer
        if self.aiml is not None:
            self.aiml.append( buf )


    def predicates( self, bot=False ):
        """
        Return session predicates (False) or bot predicates (True), as an
        iterator over (key, value) tuples
        """
        if bot:
            return self._botPredicates.iteritems()
        sdata = self.getSessionData()
        return ( (k,sdata['_global'][k]) 
                 for k in sorted(sdata['_global'].iterkeys())
                 if not k[0].startswith('_') )


    def save( self, filename, session=True, bot=True ):
        """
        Save the complete bot state (patterns, session predicates, bot
        predicates) to disk.
        We will use a .ini config file + a serialized brain file. The first
        one references the second.
        """
        cfg = ConfigParser.SafeConfigParser()

        encode = lambda s : s.encode('utf-8')

        # Session predicates
        cfg.add_section( 'session' )
        if session:
            if self._verboseMode: print('Saving session predicates... ',end='')
            num = -1
            for num, kv in enumerate(self.predicates()):
                cfg.set('session',*map(encode,kv) )
            if self._verboseMode: print(num+1,'predicates')

        # Bot predicates
        cfg.add_section( 'bot' )
        if bot:
            if self._verboseMode: print('Saving bot predicates... ',end='')
            num = -1
            for num, kv in enumerate(self.predicates(True)):
                cfg.set('bot',*map(encode,kv) )
            if self._verboseMode: print(num+1,'predicates')

        # Brain patterns
        if filename.endswith('.ini'):
            filename = filename[:-4]
        cfg.add_section( 'brain' )
        self.saveBrain( filename + '.brain' )
        cfg.set( 'brain', 'filename', os.path.basename(filename) + '.brain' )
        
        # Save main file
        filename += '.ini'
        if self._verboseMode: print( 'Writing main bot file:', filename )
        with open( filename, 'w' ) as f:
            cfg.write( f )


    def load( self, filename ):
        """
        Load the complete bot state (patterns, session predicates, bot
        predicates) from disk.
        """
        # Read INI configuration file
        cfgdir = os.path.dirname( filename )
        if not filename.endswith('.ini'):
            filename += '.ini'
        cfg = ConfigParser.SafeConfigParser()
        if len(cfg.read(filename)) != 1:
            raise KrnlException( "Can't load bot from file: {}", filename )

        decode = lambda s : s.decode('utf-8')

        # Set session predicates
        if self._verboseMode: print( 'Loading session predicates... ',end='' )
        num = -1
        for num, kv in enumerate(cfg.items('session')):
            self.setPredicate( *map(decode,kv) )
        if self._verboseMode: print(num+1,'predicates')

        # Set bot predicates
        if self._verboseMode: print( 'Loading bot predicates... ',end='' )
        num = -1
        for num, kv in enumerate(cfg.items('bot')):
            self.setBotPredicate( *map(decode,kv) )
        if self._verboseMode: print(num+1,'predicates')

        # Load brain
        filename = cfg.get('brain','filename')
        if not os.path.exists( filename ):
            filename = os.path.join( cfgdir, filename )
        self.loadBrain( filename )


    def setBotPredicate(self, name, value):
        '''
        Override parent's method to enable additional processing for
        some special bot predicates.
        '''
        super(AimlBot,self).setBotPredicate( name, value )
        if name == 'lang':
            locale.setlocale( locale.LC_ALL, str(value) )


    def _processDate(self, elem, sessionID):
        """
        Override parent's method to allow full formatting of dates,
        based on AIML patterns such as

          <date format='fmt'/>

        where "fmt" is an strftime() format specification.
        Note that date formatting is locale-dependent. Define the 'lang'
        bot predicate to change locale.
        """
        if len(elem) == 1 or 'format' not in elem[1]:
            return time.asctime()
        else:
            return time.strftime( elem[1]['format'] )


