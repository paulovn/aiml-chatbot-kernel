from __future__ import absolute_import

from ipykernel.kernelapp import IPKernelApp
from traitlets import Dict

# -----------------------------------------------------------------------

class AimlBotApp( IPKernelApp ):
    """
    The main kernel application, inheriting from the ipykernel
    """
    from .kernel import AimlBotKernel
    from .install import AimlBotInstall, AimlBotRemove
    kernel_class = AimlBotKernel

    # We override subcommands to add our own install command
    subcommands = Dict({                                                        
        'install': (AimlBotInstall, 
                    AimlBotInstall.description.splitlines()[0]), 
        'remove': (AimlBotRemove, 
                   AimlBotRemove.description.splitlines()[0]), 
    })


# -----------------------------------------------------------------------

def main():
    """
    This is the installed entry point
    """
    AimlBotApp.launch_instance()

if __name__ == '__main__':
    main()
