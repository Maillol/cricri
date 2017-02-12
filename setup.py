from setuptools import setup
import sys
import os
sys.path.insert(0, '.')
from gentest import __version__

path_to_requirements = os.path.join(os.path.dirname(__file__), 'requirements.txt')
with open(path_to_requirements, 'r') as requirements_file:
    required = requirements_file.read().splitlines()


print(required)

if 'a' in __version__:
    development_status = 'Development Status :: 3 - Alpha'
elif 'b' in __version__:
    development_status = 'Development Status :: 4 - Beta'
else:
    development_status = 'Development Status :: 5 - Production/Stable'


setup(
    name='gentest',
    version=__version__,
    description='Scenario test generator',
    keywords='scenario test generator unittest case',
    author='Vincent Maillol',
    author_email='vincent.maillol@gmail.com',
    url='https://github.com/maillol/scenario',
    license='GPLv3', 
    py_modules=['gentest'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Testing',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
    ],
    install_requires=required
)
