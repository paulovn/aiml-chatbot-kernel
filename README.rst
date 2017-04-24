AIML Chatbot kernel
===================

This is a Jupyter kernel that deploys a chatbot, implemented using the 
`python-aiml`_ package. The idea was taken from the `Calysto chatbot`_ kernel.

It has been tested with Jupyter 4.x. The code works with either Python 2.7 
or Python 3 (tested with Python 3.4)


Installation
------------

The installation process requires two steps:

1. Install the Python package::

     pip install aimlbotkernel

2. Install the kernel into Jupyter::

     jupyter aimlbotkernel install [--user] [--logdir <dir>]

The ``--user`` option will install the kernel in the current user's personal
config, while the generic command will install it as a global kernel (but
needs write permissions in the system directories).

The ``--logdir`` specifies the default place into which the logfile will be
written (unless overriden at runtime by the ``LOGDIR`` environment variable).
If no directory is specified, the (platform-specific) default temporal 
directory will be used. The logging filename is ``aimlbotkernel-<uid>.log``
where *<uid>* is the user id of the user running the notebook server. 

Note that the Jupyter kernel installation also installs some custom CSS; its 
purpose is to improve the layout of the kernel results as they are presented 
in the notebook (but it also means that the rendered notebook will look 
slightly different in a Jupyter deployment in which the kernel has not been 
installed, or within an online viewer).

To uninstall, perform the inverse operations (in reverse order), to uninstall
the kernel from Jupyter and to remove the Python package::

     jupyter aimlbotkernel remove
     pip uninstall aimlbotkernel


Operation
---------

Once installed, an *AIML Chatbot* kernel will be available in the Notebook
**New** menu. Starting one such kernel will create a chatbot. The chatbot is
initially empty but can be loaded with a couple of predefined DBs (use the 
``%help`` magic for initial instructions).


Notebook input is of two kinds:

* Regular text cells are considered human input and are sent to the chatbot,
  which produces its corresponding output
* Cells starting with ``%`` contain "magic" commands that affect the
  operation of the kernel (load AIML databases, inspecting/modifying bot
  state, saving/loading state to/from disk, etc). Use the ``%help`` magic for 
  some instructions, and ``%lsmagics`` to show the current list of defined 
  magics (magics have autocompletion and contextual help).

The `examples` directory contains a few notebooks showing some of the
provided functionality. They can also be seen with `online Notebook viewer`_
(note that, as said above, they will look slightly different than in a running 
kernel).


AIML
----

`AIML`_ is an XML-based specification to design conversational agents. Its 
most famous application is ALICE, a chatbot (the DB for the free version of 
ALICE is included in this kernel, as it is included in `python-aiml`_)

The chatbot can load an AIML database (which is basically a bunch of XML
files). It can also define AIML rules on the fly, by using the ``%aiml`` magic
in a cell.


.. _python-aiml: https://github.com/paulovn/python-aiml
.. _Calysto chatbot: https://github.com/Calysto/calysto_chatbot
.. _AIML: http://www.alicebot.org/aiml.html
.. _online Notebook viewer: http://nbviewer.jupyter.org/github/paulovn/aiml-chatbot-kernel/blob/master/examples/
