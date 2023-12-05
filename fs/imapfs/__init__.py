# coding: utf-8
"""Pyfilesystem2 over IMAP using IMAPClient.
"""

__import__("pkg_resources").declare_namespace(__name__)  # type: ignore

from .imapfs import IMAPFS
from .imapfs import Info

__all__ = ['IMAPFS', 'Info']

__license__ = "MIT"
__copyright__ = "Copyright (c) 2017-2019 Andrea Maggi"
__author__ = "Andrea Maggi <andrea@maggicontrols.com>"
__version__ = '0.2.0'
