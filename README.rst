AIML Chatbot kernel
===================

This is a Jupyter kernel that deploys a chatbot, implemented using the 
`pyAIML`_ library. The idea was taken from the `Calysto chatbot`_ kernel.

It has been tested with Python 2.7 and Jupyter 4.1

A number of magics are provided to help with loading AIML databases and 
inspecting/modifying the bot state. Use the `%help` magic for initial 
instructions.


Installation
------------

You will need Jupyter >= 4.0. The module is installable via `pip`, however
until it is uploaded to PyPI it will need to be installed from the URL.

The installation process requires two steps:

1. Install the Python package::

     pip install https://github.com/paulovn/aiml-chatbot-kernel/archive/master.zip

2. Install the kernel into Jupyter::

     jupyter aimlbotkernel install [--user]

The `--user` option will install the kernel in the current user's personal
config, while the generic command will install it as a global kernel (but
needs write permissions in the system directories).

Note that kernel installation also installs some custom CSS; its purpose is to
improve the layout of the kernel results as they are presented in the notebook
(but it also means that the rendered notebook will look slightly different in a
Jupyter deployment in which the kernel has not been installed, or within an
online viewer).

To uninstall, perform the inverse operations (in reverse order), to uninstall
the kernel from Jupyter and to remove the Python package:

     jupyter aimlbotkernel remove
     pip uninstall aimlbotkernel


Operation
---------

Once installed, an *AIML Chatbot* kernel will be available in the Notebook
**New** menu. Starting one kernel will create a chatbot. The chatbot is
initially empty but can be loaded with a couple of predefined DBs. Use the
``%help`` magic for some instructions.


AIML
----

`AIML`_ is an XML-based specification to design conversational agents. Its 
most famous application is ALICE, a chatbot (the DB for the free version of 
ALICE is included in this kernel, as it is part of pyAIML)


.. _pyAIML: https://github.com/creatorrr/pyAIML
.. _Calysto chatbot: https://github.com/Calysto/calysto_chatbot
.. _AIML: http://www.alicebot.org/aiml.html


