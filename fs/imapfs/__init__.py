# coding: utf-8
"""Pyfilesystem2 over IMAP using IMAPClient.
"""
from __future__ import absolute_import
from __future__ import unicode_literals

from .imapfs import IMAPFS
from .imapfs import Info

__all__ = ['IMAPFS', 'Info']

__license__ = "MIT"
__copyright__ = "Copyright (c) 2017-2019 Andrea Maggi"
__author__ = "Andrea Maggi <andrea@maggicontrols.com>"
__version__ = 'dev'

# import fs
# import os
# 
# result_path = os.path.realpath(
#     os.path.join(__file__, '..', '..', 'fs'))
# 
# print(result_path)
# fs.__path__.insert(0, result_path)

# Dynamically get the version of the installed module
try:
    import pkg_resources
    __version__ = pkg_resources.get_distribution(__name__).version
except Exception: # pragma: no cover
    pkg_resources = None
finally:
    del pkg_resources