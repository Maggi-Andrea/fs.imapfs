# imapfs
Pyfilesystem2 implementation for Imap

Intro
=====

This is the first release of the library.

The library has been inspired from the implememnation of the FTSFS and use internally the imapclient library (see Reference).

It's working and tested with some IMAP server.

IMAP server use a sort of file system structure and implemanting the library has been done for now some assumption that fall out of the box of the standard when you think about a file system, specially on file creation and file name.

IMAP server indeeed, when uploading a new data (an e-mail), assign to this new massage a new UID. This UID is then used as the file name.

This means that when you upload new content usimng the fs API, you specify the file name, but this will be considered, as exaple see:

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

The new file has recived UID == 1 becouse was the first one into that folder.



References
----------

* [pyfilesystem2](https://github.com/PyFilesystem/pyfilesystem2)
* [imapclient](https://github.com/mjs/imapclient)

