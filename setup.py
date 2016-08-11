"""
Install the package containing AIML Chatbot kernel for Jupyter.
To actually use the kernel in Jupyter it needs to be installed into Jupyter 
afterwards.
"""

from __future__ import print_function
import os
import os.path
import sys

from setuptools import setup


PKGNAME = 'aimlbotkernel'
GITHUB_URL = 'https://github.com/paulovn/aiml-chatbot-kernel'

pkg = __import__( PKGNAME ) 
with open('README.rst') as f:
    readme = f.read()

setup_args = dict(
    name=PKGNAME,
    version=pkg.__version__,
    description='A Chatbot kernel for Jupyter based on pyAIML',
    long_description=readme,
    license='3-clause BSD license',
    url=GITHUB_URL,
    download_url = GITHUB_URL + '/tarball/v' + pkg.__version__,
    author='Paulo Villegas',
    author_email='paulo.vllgs@gmail.com',

    packages=[ PKGNAME ],
    install_requires=[ "setuptools",
                       "ipykernel >= 4.0", 
                       "jupyter_client >= 4.0",
                       "aiml" ],

    entry_points = { 'console_scripts': [
        'jupyter-aimlbotkernel = aimlbotkernel.__main__:main',
    ]},

    include_package_data = False,       # otherwise package_data is not used
    package_data = { 
        PKGNAME : [ 'resources/logo-*x*.png', 'resources/*.css' ] 
    },

    keywords = ['AIML','chatbot','IPython','Jupyter','kernel'],
    classifiers = [
        'Framework :: IPython',
        'Programming Language :: Python :: 2 :: Only',
        'Programming Language :: Python :: 2.7',
        'License :: OSI Approved :: BSD License',
        'Development Status :: 4 - Beta',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ],
)

if __name__ == '__main__':
    setup( **setup_args )

