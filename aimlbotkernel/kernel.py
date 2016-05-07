from __future__ import print_function

import sys
import os
import aiml
import logging

from ipykernel.kernelbase import Kernel

from . import __version__
from .aimlbot import AimlBot, build_aiml
from .utils import KrnlException, data_msg



LOG = logging.getLogger( __name__ )

LOAD = { 'alice' : 'alice',
         'standard' : 'aiml b' }


general_help = """AIML Chatbot

You can start by loading a database of rules:

%learn alice | standard | <directory> | <xml-file>

For "alice" & "standard" databases, the rules will
automatically be activated. For a custom database,
you will need to launch the "load <name>" command
defined in it.

Once loaded, you can start chatting with the bot. 

New databases can be added by additiona %learn cells

Other available magics are:


%help
%forget
%aiml
%show categories
%show session

"""


# -----------------------------------------------------------------------

class ChatbotKernel(Kernel):

    implementation = 'Chatbot'
    implementation_version = __version__

    language = 'xml'
    language_version = '0.1'
    banner = "AIML Chatbot - a chatbot for Jupyter"
    language_info = { 'name': 'Chatbot', 'mimetype': 'text/xml'}


    def __init__(self, *args, **kwargs):
        # Start base kernel
        super(ChatbotKernel, self).__init__(*args, **kwargs)
        # Redirect stdout
        try:
            sys.stdout.write = self._send_stdout
        except:
            LOG.warn( "can't redirect stdout" )
        # Start the AIML kernel
        self.bot = AimlBot()
        self._l = False  


    # -----------------------------------------------------------------


    def _send( self, data, status='ok', silent=False ):
        """
        Send a response to the frontend and return an execute message
        """
        # Data to send back
        if data is not None and not silent:
            LOG.warn( ' sending: %s', data )
            # Format the data
            if isinstance(data,KrnlException):
                data = data()
            else:
                data = data_msg( data, mtype=status )
            # Send the data to the frontend
            self.send_response( self.iopub_socket, 'display_data', data )

        # Result message
        return {'status': 'error' if status == 'error' else 'ok',
                # The base class will increment the execution count
                'execution_count': self.execution_count,
                'payload' : [],
                'user_expressions': {},
               }


    def _send_stdout(self, txt):
        """
        Send to frontend the data received as stdout
        """
        stream_content = { 'name': 'stdout', 'text': txt, 'metadata': {} }
        LOG.debug('stdout: %s' % txt)
        self.send_response(self.iopub_socket, 'stream', stream_content)


    def learn_file( self, name ):
        """
        Load rules from AIML files
        """
        # A direct file to load
        if name.endswith('.xml') or name.endswith('aiml'):
            self._send( ("Learning patterns in {}", name), 'ctrl' )
            self.bot.learn( name )
            self._l = True
            return

        # A directory containing AIML files + a startup file
        if name in ('alice','standard'):
            dbdir = os.path.join( os.path.dirname(aiml.__file__), name )
        elif os.path.isdir( name ):
            if not os.path.isfile( os.path.join(name,'startup.xml') ):
                raise KrnlException( "Error: missing startup file in '{}", name)
        else:
            raise KrnlException( 'unimplemented learn for {}', name )
        
        self._send( ("Learning database: '{}'", name), status='ctrl' )
        prev = os.getcwd()
        try:
            LOG.warn( 'find %s',dbdir)
            os.chdir( dbdir )
            LOG.warn( 'learn' )
            self.bot.learn( 'startup.xml' )
            self._l = True
            if LOAD.get(name ):
                LOG.warn( 'load '+ LOAD[name] )
                self._send( "Loading patterns", 'ctrl' )
                self.bot.respond( 'load ' + LOAD[name] )
                return "Patterns loaded"
        finally:
            os.chdir( prev )


    def learn_cell( self, code ):
        """
        Learn rules from a notebook cell
        """
        # Get all non-comment, non-magic lines
        lines = [ l.strip() for l in code.split('\n') 
                  if not l or l[0] not in ('#','%') ]
        # Skip initial empty lines
        for i, l in enumerate(lines):
            if l: break
        lines = lines[i:]
        # Learn the passed code
        if lines[0][0] == '<':
            self.bot.learn_buffer( lines )
        else:
            self.bot.learn_buffer( build_aiml(lines) )
        
        
    def _inner_execute( self, code, silent ):
        """
        Execute the cell code, send the appropriate message to the frontend
        and return the result
        """
        LOG.warn( 'CODE: %s', code )
        if code in ('%?','%help') or (not self._l and 0 and 
                                      (len(code)==0 or code[0] != '%')):
            return self._send( general_help, 'help' )
            
        elif code.startswith("%learn"):

            kw = code.split(None,1)
            if len(kw) < 2:
                raise KrnlException( 'missing learn param' )                
            return self._send( self.learn_file(kw[1]), 'ctrl' )

        elif code.startswith("%aiml"):

            return self._send( self.learn_cell(code), 'learn' )

        elif code.startswith("%forget") or code.startswith('%reset'):

            self.bot.resetBrain()
            self._l = False
            return self._send( 'Resetting bot brain', 'ctrl' )

        elif code.startswith("%show cat"):
            msg = "Number of loaded categories: {}", self.bot.numCategories()
            return self._send( msg, 'info' )

        elif code.startswith("%show ses"):

            sdata = self.bot.getSessionData()
            fields = [ '  {}: {}'.format(k,sdata['_global'][k]) 
                       for k in sorted(sdata['_global'].iterkeys())
                       if not i[0].startswith('_') ]
            return self._send( "Session fields:\n" + "\n".join(fields), 'info' )

        elif code.startswith("%"):

            raise KrnlException( 'unknown magic: {}', code )

        else:
            return self._send( self.bot.respond(code), 'ok' )



    def do_execute( self, code, silent, store_history=True,
                    user_expressions=None, allow_stdin=False ):

        try:
            return self._inner_execute( code, silent )
        except KrnlException as e:
            return self._send( e, silent=silent, status='error' )
        except Exception as e:
            #raise
            return self._send( KrnlException(e), silent=silent, status='error' )
            

