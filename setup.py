from setuptools import setup
import sys
import os
sys.path.insert(0, './cricri')
from __version__ import __version__


if 'a' in __version__:
    development_status = 'Development Status :: 3 - Alpha'
elif 'b' in __version__:
    development_status = 'Development Status :: 4 - Beta'
else:
    development_status = 'Development Status :: 5 - Production/Stable'


setup(
    name='cricri',
    version=__version__,
    description='Scenario test generator',
    keywords='scenario test generator unittest case',
    author='Vincent Maillol',
    author_email='vincent.maillol@gmail.com',
    url='https://github.com/maillol/scenario',
    license='GPLv3', 
    packages=['cricri'],
    classifiers=[
        development_status,
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Testing',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
    ],
    install_requires=['voluptuous']
)
