import sys
import unicodedata
from xml.sax import parseString, SAXParseException
from aiml import Kernel
from aiml.AimlParser import AimlHandler



def normalize_string(input_str):
    """
    Normalize a string, removing diacritical characters (mapping
    them to the closest equivalent char)
    """
    # http://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string
    # http://stackoverflow.com/questions/4162603/python-and-character-normalization
    nkfd_form = unicodedata.normalize('NFKD', unicode(input_str))
    return nkfd_form.encode('iso8859-1','ignore')
    #return u"".join( [c for c in nkfd_form if not unicodedata.combining(c)] )


def split_rules( lines ):
    rule = []
    for l in lines:
        if l:
            rule.append( l )
        elif rule:
            yield rule
            rule = []
    if rule:
        yield rule



def build_aiml( lines ):
    print lines
    aiml = u'<?xml version="1.0" encoding="utf-8"?><aiml version="1.0">'
    for rule in split_rules(lines):
        if len(rule)<2:
            raise RuntimeException('invalid rule:\n' + '\n'.join(rule) )
        aiml += u'<category><pattern>{}</pattern>'.format(rule[0].upper())
        if rule[1].startswith('<that>'):
            aiml += rule[1]
            if not rule[1].endswith('</that>'):
                aiml += '</that>'
            rule = rule[1:]
        aiml += '<template>{}</template></category>'.format('\n'.join(rule[1:]))
    aiml += u'</aiml>'
    print aiml.encode('utf-8')
    return aiml.encode('utf-8')


# -------------------------------------------------------------------------

class AimlBot( Kernel, object ):
    """
    A subclass of the standard AIML kernel, with the added functionality
    of being able to slurp a string buffer containing AIML statements
    """
    
    def __init__( self, *args, **kwargs ):
        super( AimlBot, self ).__init__()
        self.setTextEncoding( 'utf-8' )
        if 'name' in kwargs:
            self.setPredicate( 'name', kwargs['name'] )

    def learn_buffer( self, string ):
        """
        Learn the AIML stored a string buffer
        """
        # Load and parse the AIML file.                                     
        handler = AimlHandler("UTF-8")
        handler.setEncoding( self._textEncoding )
        try: 
            parseString(string,handler)
        except SAXParseException, msg:
            err = "\nFATAL PARSE ERROR: %s\n" % msg
            sys.stdout.write(err)
            return
        # store the pattern/template pairs in the PatternMgr.               
        for key,tem in handler.categories.items():
            self._brain.add(key,tem)
        self._brain.dump()


