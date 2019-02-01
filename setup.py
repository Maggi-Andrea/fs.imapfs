'''
Created on 01 feb 2019

@author: Andrea
'''
from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()


setup(name='funniest',
      version='0.1',
      description='Pyfilesystem2 implementation for Imap',
      long_description=readme(),
      classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Filesystems',
      ],
      keywords='filesystem, Pyfilesystem2, imap',
      url='http://github.com/superAndre/imapfs',
      author='Andrea Maggi',
      author_email='andrea@maggicontrols.com',
      license='MIT',
      packages=['fs.imapfs'],
      install_requires=[
          'fs==2.2.1'
          'IMAPClient',
      ],
      test_suite='tests',
      tests_require=['fs.imapfs[test]'],
      entry_points={
          'console_scripts': ['funniest-joke=funniest.command_line:main'],
      },
      include_package_data=True,
      zip_safe=False)