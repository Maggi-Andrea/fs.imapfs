# coding: utf-8
"""Pyfilesystem2 over IMAP using IMAPClient.
"""
from __future__ import absolute_import
from __future__ import unicode_literals

from .imapfs import IMAPFS

__all__ = ['IMAPFS']

__license__ = "MIT"
__copyright__ = "Copyright (c) 2017-2019 Andrea Maggi"
__author__ = "Martin Larralde <andrea@maggicontrols.com>"
__version__ = 'dev'

# Dynamically get the version of the installed module
try:
    import pkg_resources
    __version__ = pkg_resources.get_distribution(__name__).version
except Exception: # pragma: no cover
    pkg_resources = None
finally:
    del pkg_resources