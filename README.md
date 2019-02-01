# fs.imapfs
Pyfilesystem2 implementation for Imap

Installation
------------

Install directly from PyPI, using [pip](https://pip.pypa.io)

    pip install fs.imapfs

Intro
=====

This is the first release of the library. The implemantation is at its early stage. The module is not jet ready to be installed: setup module is missing and no opener implemented. Apart from that, the module is fully working.

The library has been inspired from the implementation of the FTSFS and use internally the imapclient library (see Reference).

It's working and tested with some IMAP server.

IMAP server use a sort of file system structure and implementing the library has been done for now some assumption that fall out of the box of the standard when you think about a file system, specially on file creation and file name.

IMAP server indeed, when uploading a new data (an e-mail), assign to this new massage a new UID. This UID is then used as the file name.

This means that when you upload new content using the fs API, you specify the file name, but this will be considered, as example see:

```python
imap_fs.tree()
`-- INBOX
    |-- Archivie
    |-- Draft
    |-- Posta Indesiderata
    |-- Spedite
    |-- TEST
    |-- Trash
    |-- 2.eml
    `-- 5.eml
imap_fs.setbytes(path='INBOX/TEST/2.eml', contents=b'Test')
imap_fs.tree()
`-- INBOX
    |-- Archivie
    |-- Draft
    |-- Posta Indesiderata
    |-- Spedite
    |-- TEST
    |   `-- 1.eml
    |-- Trash
    |-- 2.eml
    `-- 5.eml
```

The new file has received UID == 1 because was the first one into that folder.



References
----------

* [pyfilesystem2](https://github.com/PyFilesystem/pyfilesystem2)
* [imapclient](https://github.com/mjs/imapclient)

