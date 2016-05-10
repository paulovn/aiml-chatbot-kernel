import os
import os.path
import json
import sys
import pkgutil

from distutils.command.install import install
from distutils.core import setup
from distutils import log

from IPython.utils.path import ensure_dir_exists

PKGNAME = 'aimlbotkernel'

kernel_json = {
    "argv": [sys.executable, 
	     "-m", PKGNAME, 
	     "-f", "{connection_file}"],
    "display_name": "AIML Chatbot",
    "name": "aiml_chatbot",
    "language": "chatbot",  
    "codemirror_mode":  {
        "version": 2,
	"name": "xml"
    }
}


# --------------------------------------------------------------------------

def copyresource( resource, filename, destdir ):
    """
    Copy a resource file to a destination
    """
    data = pkgutil.get_data(resource, os.path.join('resources',filename) )
    print "Installing ", os.path.join(destdir,filename)
    with open( os.path.join(destdir,filename), 'wb' ) as fp:
        fp.write(data)


def install_custom_css(destdir, cssfile, resource=PKGNAME ):
    """
    Install the custom CSS file and include it within custom.css
    """
    # Copy it
    ensure_dir_exists( destdir )
    cssfile += '.css'
    copyresource( resource, cssfile, destdir )

    # Check if custom.css already includes it. If so, we can return
    include = "@import url('{}');".format( cssfile )
    custom = os.path.join( destdir, 'custom.css' )
    if os.path.exists( custom ):
        with open(custom) as f:
            for line in f:
                if line.find( include ) >= 0:
                    return

    # Add the import line at the beginning of custom.css
    with open(custom + '-new', 'w') as fout:
        fout.write('/* --- Added for {} --- */\n'.format(resource) )
        fout.write( include + '\n' )
        fout.write('/* ----------------------------- */\n'.format(resource) )
        with open( custom ) as fin:
            for line in fin:
                fout.write( line )
    os.rename( custom+'-new',custom)



def install_kernel_resources( destdir, resource=PKGNAME, files=None ):
    """
    Copy the resource files to the kernelspec folder.
    """
    if files is None:
        files = ['logo-64x64.png', 'logo-32x32.png']
    for filename in files:
        try:
            copyresource( resource, filename, destdir )
        except Exception as e:
            sys.stderr.write(str(e))


# --------------------------------------------------------------------------

class install_with_kernelspec(install):

    def run(self):
        # Regular package installation
        install.run(self)

        # Now write the kernelspec
        from jupyter_client.kernelspec import KernelSpecManager
        from IPython.utils.tempdir import TemporaryDirectory
        mgr = KernelSpecManager()
        log.info( "Kernel dirs: %s", mgr.kernel_dirs )
        with TemporaryDirectory() as td:
            os.chmod(td, 0o755) # Starts off as 700, not user readable
            with open(os.path.join(td, 'kernel.json'), 'w') as f:
                json.dump(kernel_json, f, sort_keys=True)
            install_kernel_resources(td, resource=PKGNAME)
            log.info('Installing kernel spec')
            try:
                log.info('trying system')
                mgr.install_kernel_spec(td, PKGNAME, replace=True)
            except:
                log.info('trying user %s', self.user)
                mgr.install_kernel_spec(td, PKGNAME, user=True, replace=True)
        # Install the css
        # Use the ~/.jupyter/custom dir
        import jupyter_core
        destd = os.path.join( jupyter_core.paths.jupyter_config_dir(),'custom')
        # Use the system custom dir
        #import notebook
        #destd = os.path.join( notebook.DEFAULT_STATIC_FILES_PATH, 'custom' )
        install_custom_css( destd, PKGNAME )



# --------------------------------------------------------------------------

svem_flag = '--single-version-externally-managed'
if svem_flag in sys.argv:
    # Die, setuptools, die.
    sys.argv.remove(svem_flag)

pkg = __import__( PKGNAME ) 
with open('README.md') as f:
    readme = f.read()

setup(name=PKGNAME,
      version=pkg.__version__,
      description='A Chatbot kernel for Jupyter based on pyAIML',
      long_description=readme,
      url="https://github.com/paulovn/aiml-chatbot-kernel",
      author='Paulo Villegas',
      author_email='paulo.vllgs@gmail.com',
      packages=[ PKGNAME ],
      install_requires=[ "aiml" ],
      cmdclass={'install': install_with_kernelspec},
      classifiers = [
          'Framework :: IPython',
          'License :: OSI Approved :: BSD License',
          'Programming Language :: Python :: 2',
      ]
)
