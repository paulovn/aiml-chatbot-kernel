AIML Chatbot kernel
===================

This is a Jupyter kernel that deploys a chatbot, implemented using the 
`pyAIML`_ library. The idea was taken from the `Calysto chatbot`_ kernel.

It has been tested with Python 2.7 and Jupyter 4.1. It will not work with
Python 3.


Installation
------------

You will need Jupyter >= 4.0. The module is installable via `pip`, however
until it is uploaded to PyPI it will need to be installed from the URL.

The installation process requires two steps:

1. Install the Python package::

     pip install aimlbotkernel

2. Install the kernel into Jupyter::

     jupyter aimlbotkernel install [--user]

The ``--user`` option will install the kernel in the current user's personal
config, while the generic command will install it as a global kernel (but
needs write permissions in the system directories).

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

The `examples`_ directory contains a few notebooks showing some of the
provided functionality.


AIML
----

`AIML`_ is an XML-based specification to design conversational agents. Its 
most famous application is ALICE, a chatbot (the DB for the free version of 
ALICE is included in this kernel, as it is part of pyAIML)

The chatbot can load an AIML database (which is basically a bunch of XML
files). It can also define AIML rules on the fly, by using the ``%aiml`` magic
in a cell.


.. _pyAIML: https://github.com/creatorrr/pyAIML
.. _Calysto chatbot: https://github.com/Calysto/calysto_chatbot
.. _AIML: http://www.alicebot.org/aiml.html
.. _examples: examples/


