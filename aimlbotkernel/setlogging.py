"""
Install a logging configuration for kernel modules
"""


from logging.config import dictConfig
import tempfile
import os
import os.path


# ----------------------------------------------------------------------

LOGCONFIG = {
    'version' : 1,
    'formatters' : {
        'default' : { 'format': 
                      '%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s' }
        },

    'handlers' : {
        'default' : { 'level' : 'DEBUG',
                      'class' : 'logging.handlers.RotatingFileHandler',
                      'formatter': 'default',
                      'filename': None,
                      'maxBytes': 1000000,
                      'backupCount': 3 }
        },

    'loggers' : { 
                  # the parent logger for sparqlkernel modules
                  'sparqlkernel' : { 'level' : 'INFO',
                                     'propagate' : False,
                                     'handlers' : ['default'] },

                  # This is the logger for the base kernel app
                  'IPKernelApp' : { 'level' : 'INFO',
                                    'propagate' : False,
                                    'handlers' : ['default'] },
              },

    # root logger
    'root' : { 'level': 'WARN',
               'handlers' : [ 'default' ]
        },
}


# ----------------------------------------------------------------------

def set_logging( logfilename=None, level=None ):
    """
    Set a logging configuration, with a rolling file appender.
    If passed a filename, use it as the logfile, else use a default name.

    The default logfile is \c aimlbotkernel-<uid>.log, placed in the directory 
    given by (in this order) the \c LOGDIR environment variable, the logdir
    specified upon kernel installation or the default temporal directory.
    """
    if logfilename is None:
        # Find the logging diectory
        # [1] LOGDIR environment variable
        logdir = os.environ.get( 'LOGDIR' )
        # [2] directory set upon kernel installation or [3] tmpdir
        if logdir is None:
            logdir = os.environ.get( 'LOGDIR_DEFAULT', tempfile.gettempdir() )
        # Define the log filename
        basename = __name__.split('.')[-2]
        try:
            logname = '{}-{}.log'.format( basename, os.getuid() )
        except Exception:
            logname = '{}.log'.format( basename )
        logfilename = os.path.join( logdir, logname )
    
    LOGCONFIG['handlers']['default']['filename'] = logfilename
    if level is not None:
        LOGCONFIG['loggers']['sparqlkernel']['level'] = level
    dictConfig( LOGCONFIG )


def logfilename():
    '''
    Return the name of the logfile
    '''
    if LOGCONFIG['handlers']['default']['filename'] is None:
        set_logging()
    return LOGCONFIG['handlers']['default']['filename']

