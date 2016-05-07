
if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    from .kernel import ChatbotKernel
    IPKernelApp.launch_instance( kernel_class=ChatbotKernel )
