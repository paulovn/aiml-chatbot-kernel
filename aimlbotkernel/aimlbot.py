"""
An extension over pyAIML's Kernel class, to add some modifications:
 * allow parsing of AIML documents contained in a buffer, 
 * allow also parsing a somehow simplified plain-text-like format (to ease 
   writing AIML rules)
 * allow iterating over predicates (either session or bot predicates).
 * load/save full bot states (not only brain, but also session, bot predicates
   and substitutions)
 * define substitutions from iterables
 * improve date rendering by adding strftime() formatting, locale-dependent
 * set locale by defining the \c lang bot predicate
 * add a 'trace' command that processes input keeping the stack of evaluated
   elements
"""

from __future__ import absolute_import, division, print_function

import sys
import os.path
import logging
import re
import locale
import datetime
import time
import unicodedata
import ConfigParser
from functools import partial
from itertools import count

from xml.sax import parseString, SAXParseException
from aiml import Kernel
from aiml.AimlParser import AimlHandler
from aiml.WordSub import WordSub

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
    # Split between XML markup and text; clean up text fragments
    fragments = (f if f.startswith('<') else re.sub(repl,' ',f).upper()
                 for f in re.split( r'(<[^>]+>)',g.group(1)) )
    return ''.join( fragments )



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
    fsrai = partial( srai_sub, re_clean ) if re_clean else None
    for rule in split_rules(lines):
        if len(rule)<2:
            raise KrnlException( u'invalid rule:\n{}', u'\n'.join(rule) )
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
        if fsrai:
            tpl = re.sub( '(<srai>.+</srai>)', fsrai, tpl )
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
        self._aiml = None
        # This is for the trace command
        self._traceStack = None

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
        if self._aiml is not None:
            self._aiml.append( buf )


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


    def addSub( self, name, items, reset=False ):
        ''' 
        Add a new WordSub instance
          @param name (str): Wordsub name
          @param items (iterable of tuples): subs to add
          @param reset (bool): delete all current subs in this WordSub
          @return (int): number of subs added
        '''
        # Just define default (English) subbers
        if name == 'default':
            import aiml.DefaultSubs as DefaultSubs
            self._subbers = {}
            self._subbers['gender'] = WordSub(DefaultSubs.defaultGender)
            self._subbers['person'] = WordSub(DefaultSubs.defaultPerson)
            self._subbers['person2'] = WordSub(DefaultSubs.defaultPerson2)
            self._subbers['normal'] = WordSub(DefaultSubs.defaultNormal)
            return 'default subs defined'

        # Reset current dictionary, if requested
        if reset and name in self._subbers:
            del self._subbers[name]
        # and ensure it exists
        if name not in self._subbers:
            self._subbers[name] = WordSub()
        # Add all subs
        n = -1
        for n, kv in enumerate(items):
            #print("Sub", n+1, kv)
            self._subbers[name][kv[0]] = kv[1]
        # We need at least one, or substitution will crash
        if n == -1:
            self._subbers[name]['DUMMYSUB'] = 'DUMMYSUB'
        return n+1


    def save( self, filename, options=[] ):
        """
        Save the complete bot state (patterns, session predicates, bot
        predicates, subs) to disk. Any of those data elements can be skipped.

          @param filename (str): name of file to save to (appropriate suffixes 
            will be added)
          @param options (list): options to select what gets saved

        We will use a .ini config file + a serialized brain file. The first
        one references the second.
        """
        options = set( (v[:5] for v in options) )
        cfg = ConfigParser.SafeConfigParser()
        cfg.add_section( 'general' )
        cfg.set( 'general', 'date', 
                 datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z') )
        encode = lambda s : s.encode('utf-8')

        # Session predicates
        cfg.add_section( 'session' )
        if 'noses' in options:
            if self._verboseMode: print('Skipping session predicates')
        else:
            if self._verboseMode: print('Saving session predicates... ',end='')
            num = -1
            for num, kv in enumerate(self.predicates()):
                cfg.set('session',*map(encode,kv) )
            if self._verboseMode: print(num+1,'predicates')

        # Bot predicates
        cfg.add_section( 'bot' )
        if 'nobot' in options:
            if self._verboseMode: print('Skipping bot predicates')
        else:
            if self._verboseMode: print('Saving bot predicates... ',end='')
            num = -1
            for num, kv in enumerate(self.predicates(True)):
                cfg.set('bot',*map(encode,kv) )
            if self._verboseMode: print(num+1,'predicates')

        # Subs
        if 'nosub' in options:
            if self._verboseMode: print('Skipping subs')
        else:
            subs = []
            for name,s in self._subbers.iteritems():
                # Create the section
                sname = 'sub/' + name
                cfg.add_section( sname )
                if self._verboseMode: 
                    print('Saving subbers for {} ... '.format(name),end='')
                # Add all subs (uppercase versions will be collapsed)
                for kv in s.iteritems():
                    cfg.set(sname,*map(encode,kv) )
                num = len(cfg.options(sname))
                if self._verboseMode: print(num,'subs')
                if num>= 0:
                    subs.append( name )
            cfg.set( 'general', 'subs', ','.join(subs) )

        # Brain patterns
        if 'nobra' in options:
            if self._verboseMode: print('Skipping brain patterns')
        else:
            if filename.endswith('.ini'):
                filename = filename[:-4]
            self.saveBrain( filename + '.brain' )
            cfg.set( 'general', 'brain-filename', 
                     os.path.basename(filename) + '.brain' )
        
        # Save main file
        filename += '.ini'
        if self._verboseMode: print( 'Writing main bot file:', filename )
        with open( filename, 'w' ) as f:
            cfg.write( f )


    def load( self, filename, options=[] ):
        """
        Load the complete bot state (patterns, session predicates, bot
        predicates) from disk.
        """
        options = set( (v[:5] for v in options) )

        # Read INI configuration file
        cfgdir = os.path.dirname( filename )
        if not filename.endswith('.ini'):
            filename += '.ini'
        cfg = ConfigParser.SafeConfigParser()
        if len(cfg.read(filename)) != 1:
            raise KrnlException( "Can't load state from file: {}", filename )

        decode = lambda s : s.decode('utf-8')

        # Set session predicates
        if 'noses' in options:
            if self._verboseMode: print('Skipping session predicates')
        else:
            if self._verboseMode: print('Loading session predicates... ',end='')
            num = -1
            for num, kv in enumerate(cfg.items('session')):
                self.setPredicate( *map(decode,kv) )
            if self._verboseMode: print(num+1,'predicates')

        # Set bot predicates
        if 'nobot' in options:
            if self._verboseMode: print('Skipping bot predicates')
        else:
            if self._verboseMode: print( 'Loading bot predicates... ',end='' )
            num = -1
            for num, kv in enumerate(cfg.items('bot')):
                self.setBotPredicate( *map(decode,kv) )
            if self._verboseMode: print(num+1,'predicates')

        # Load subs
        if 'nosub' in options:
            if self._verboseMode: print('Skipping subs')
        else:
            try:
                for sub in cfg.get('general','subs').split(','): 
                    if self._verboseMode: 
                        print('Loading subs for {} ... '.format(sub), end='' )
                    n = self.addSub( sub, cfg.items('sub/'+sub), reset=True )
                    if self._verboseMode: print(n,'subs')
            except ConfigParser.NoOptionError:
                if self._verboseMode: print('No subs defined')

        # Load brain
        if 'nobot' in options:
            if self._verboseMode: print('Skipping brain patterns')
        else:
            try:
                filename = cfg.get('general','filename')
                if not os.path.exists( filename ):
                    filename = os.path.join( cfgdir, filename )
                self.loadBrain( filename )
            except ConfigParser.NoOptionError:
                if self._verboseMode: print('No brain file defined')


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


    def trace( self, inputMsg ):
        '''
        Process an input, but keeping track of all the elements processed
        '''
        bck = self._processElement_Trace, self._respond_Trace
        self._traceStack = []

        try:
            self._processElement = self._processElement_Trace
            self._respond = self._respond_Trace
            result = self.respond( inputMsg.encode('utf-8') ).decode('utf-8')
            import pprint
            n = count(1)
            tr = [ (m[1],m[0]) if m[0].startswith('trace-') else
                   ('{:2}: {}\n'.format(n.next(),m[0])+pprint.pformat(m[1:]),
                    'trace-res') for m in self._traceStack ]
            return tr + [(result,'bot')]
        finally:
            self._processElement, self._respond = bck
            self._traceStack = []


    def _respond_Trace(self, input, sessionID):
        # Find topic & that
        topic = self._subbers['normal'].sub( self.getPredicate("topic") )
        outHist = self.getPredicate(self._outputHistory)
        that = self._subbers['normal'].sub( outHist[-1] if outHist else '' )
        # Add the inputs to the stack
        dat = ( 'trace-in', 
                u'INPUT=[{}] THAT=[{}] TOPIC=[{}]'.format(input,that,topic) )
        self._traceStack.append( dat )
        # Route to parent
        return super(AimlBot,self)._respond( input, sessionID )


    def _processElement_Trace(self,elem, sessionID):
        # Add the element to the stack
        self._traceStack.append( elem )
        # Route to parent
        return super(AimlBot,self)._processElement( elem, sessionID )


