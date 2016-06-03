from __future__ import print_function
import os
import os.path
import sys

from setuptools import setup

from IPython.utils.path import ensure_dir_exists



PKGNAME = 'aimlbotkernel'

pkg = __import__( PKGNAME ) 
with open('README.rst') as f:
    readme = f.read()

setup_args = dict (
    name=PKGNAME,
    version=pkg.__version__,
    description='A Chatbot kernel for Jupyter based on pyAIML',
    long_description=readme,
    url="https://github.com/paulovn/aiml-chatbot-kernel",
    author='Paulo Villegas',
    author_email='paulo.vllgs@gmail.com',
    packages=[ PKGNAME ],
    install_requires=[ "ipykernel >= 4.0", 
                       "jupyter_client >= 4.0",
                       "setuptools", 
                       "aiml" ],
    entry_points = { 'console_scripts': [
        'jupyter-aimlbotkernel = aimlbotkernel.__main__:main',
    ]},
    license='3-clause BSD license',
    package_data = { PKGNAME : [ 'resources/logo-*x*.png', 
                                 'resources/*.css' ] },
    include_package_data = True,
)

if __name__ == '__main__':
    setup( **setup_args )

