'''
Created on 06 dic 2018

@author: Andrea
'''
import unittest

from imaplib import IMAP4

from fs.test import FSTestCases


import collections
from datetime import datetime
import io
import itertools
import json
import math
import os
import time
# 
import fs.copy
import fs.move
from fs.enums import ResourceType
from fs.enums import Seek
from fs import errors
from fs import walk
from fs import glob
from fs.opener import open_fs
from fs.subfs import SubFS
from fs.subfs import ClosingSubFS 
# 
import pytz
import six
from six import text_type

from fs.imapfs import IMAPFS as IMAPFS

UNICODE_TEXT = """

UTF-8 encoded sample plain-text file
‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾

Markus Kuhn [ˈmaʳkʊs kuːn] &lt;mkuhn@acm.org> — 1999-08-20


The ASCII compatible UTF-8 encoding of ISO 10646 and Unicode
plain-text files is defined in RFC 2279 and in ISO 10646-1 Annex R.


Using Unicode/UTF-8, you can write in emails and source code things such as

Mathematics and Sciences:

  ∮ E⋅da = Q,  n → ∞, ∑ f(i) = ∏ g(i), ∀x∈ℝ: ⌈x⌉ = −⌊−x⌋, α ∧ ¬β = ¬(¬α ∨ β),

  ℕ ⊆ ℕ₀ ⊂ ℤ ⊂ ℚ ⊂ ℝ ⊂ ℂ, ⊥ &lt; a ≠ b ≡ c ≤ d ≪ ⊤ ⇒ (A ⇔ B),

  2H₂ + O₂ ⇌ 2H₂O, R = 4.7 kΩ, ⌀ 200 mm

Linguistics and dictionaries:

  ði ıntəˈnæʃənəl fəˈnɛtık əsoʊsiˈeıʃn
  Y [ˈʏpsilɔn], Yen [jɛn], Yoga [ˈjoːgɑ]

APL:

  ((V⍳V)=⍳⍴V)/V←,V    ⌷←⍳→⍴∆∇⊃‾⍎⍕⌈

Nicer typography in plain text files:

  ╔══════════════════════════════════════════╗
  ║                                          ║
  ║   • ‘single’ and “double” quotes         ║
  ║                                          ║
  ║   • Curly apostrophes: “We’ve been here” ║
  ║                                          ║
  ║   • Latin-1 apostrophe and accents: '´`  ║
  ║                                          ║
  ║   • ‚deutsche‘ „Anführungszeichen“       ║
  ║                                          ║
  ║   • †, ‡, ‰, •, 3–4, —, −5/+5, ™, …      ║
  ║                                          ║
  ║   • ASCII safety test: 1lI|, 0OD, 8B     ║
  ║                      ╭─────────╮         ║
  ║   • the euro symbol: │ 14.95 € │         ║
  ║                      ╰─────────╯         ║
  ╚══════════════════════════════════════════╝

Greek (in Polytonic):

  The Greek anthem:

  Σὲ γνωρίζω ἀπὸ τὴν κόψη
  τοῦ σπαθιοῦ τὴν τρομερή,
  σὲ γνωρίζω ἀπὸ τὴν ὄψη
  ποὺ μὲ βία μετράει τὴ γῆ.

  ᾿Απ᾿ τὰ κόκκαλα βγαλμένη
  τῶν ῾Ελλήνων τὰ ἱερά
  καὶ σὰν πρῶτα ἀνδρειωμένη
  χαῖρε, ὦ χαῖρε, ᾿Ελευθεριά!

  From a speech of Demosthenes in the 4th century BC:

  Οὐχὶ ταὐτὰ παρίσταταί μοι γιγνώσκειν, ὦ ἄνδρες ᾿Αθηναῖοι,
  ὅταν τ᾿ εἰς τὰ πράγματα ἀποβλέψω καὶ ὅταν πρὸς τοὺς
  λόγους οὓς ἀκούω· τοὺς μὲν γὰρ λόγους περὶ τοῦ
  τιμωρήσασθαι Φίλιππον ὁρῶ γιγνομένους, τὰ δὲ πράγματ᾿
  εἰς τοῦτο προήκοντα,  ὥσθ᾿ ὅπως μὴ πεισόμεθ᾿ αὐτοὶ
  πρότερον κακῶς σκέψασθαι δέον. οὐδέν οὖν ἄλλο μοι δοκοῦσιν
  οἱ τὰ τοιαῦτα λέγοντες ἢ τὴν ὑπόθεσιν, περὶ ἧς βουλεύεσθαι,
  οὐχὶ τὴν οὖσαν παριστάντες ὑμῖν ἁμαρτάνειν. ἐγὼ δέ, ὅτι μέν
  ποτ᾿ ἐξῆν τῇ πόλει καὶ τὰ αὑτῆς ἔχειν ἀσφαλῶς καὶ Φίλιππον
  τιμωρήσασθαι, καὶ μάλ᾿ ἀκριβῶς οἶδα· ἐπ᾿ ἐμοῦ γάρ, οὐ πάλαι
  γέγονεν ταῦτ᾿ ἀμφότερα· νῦν μέντοι πέπεισμαι τοῦθ᾿ ἱκανὸν
  προλαβεῖν ἡμῖν εἶναι τὴν πρώτην, ὅπως τοὺς συμμάχους
  σώσομεν. ἐὰν γὰρ τοῦτο βεβαίως ὑπάρξῃ, τότε καὶ περὶ τοῦ
  τίνα τιμωρήσεταί τις καὶ ὃν τρόπον ἐξέσται σκοπεῖν· πρὶν δὲ
  τὴν ἀρχὴν ὀρθῶς ὑποθέσθαι, μάταιον ἡγοῦμαι περὶ τῆς
  τελευτῆς ὁντινοῦν ποιεῖσθαι λόγον.

  Δημοσθένους, Γ´ ᾿Ολυνθιακὸς

Georgian:

  From a Unicode conference invitation:

  გთხოვთ ახლავე გაიაროთ რეგისტრაცია Unicode-ის მეათე საერთაშორისო
  კონფერენციაზე დასასწრებად, რომელიც გაიმართება 10-12 მარტს,
  ქ. მაინცში, გერმანიაში. კონფერენცია შეჰკრებს ერთად მსოფლიოს
  ექსპერტებს ისეთ დარგებში როგორიცაა ინტერნეტი და Unicode-ი,
  ინტერნაციონალიზაცია და ლოკალიზაცია, Unicode-ის გამოყენება
  ოპერაციულ სისტემებსა, და გამოყენებით პროგრამებში, შრიფტებში,
  ტექსტების დამუშავებასა და მრავალენოვან კომპიუტერულ სისტემებში.

Russian:

  From a Unicode conference invitation:

  Зарегистрируйтесь сейчас на Десятую Международную Конференцию по
  Unicode, которая состоится 10-12 марта 1997 года в Майнце в Германии.
  Конференция соберет широкий круг экспертов по  вопросам глобального
  Интернета и Unicode, локализации и интернационализации, воплощению и
  применению Unicode в различных операционных системах и программных
  приложениях, шрифтах, верстке и многоязычных компьютерных системах.

Thai (UCS Level 2):

  Excerpt from a poetry on The Romance of The Three Kingdoms (a Chinese
  classic 'San Gua'):

  [----------------------------|------------------------]
    ๏ แผ่นดินฮั่นเสื่อมโทรมแสนสังเวช  พระปกเกศกองบู๊กู้ขึ้นใหม่
  สิบสองกษัตริย์ก่อนหน้าแลถัดไป       สององค์ไซร้โง่เขลาเบาปัญญา
    ทรงนับถือขันทีเป็นที่พึ่ง           บ้านเมืองจึงวิปริตเป็นนักหนา
  โฮจิ๋นเรียกทัพทั่วหัวเมืองมา         หมายจะฆ่ามดชั่วตัวสำคัญ
    เหมือนขับไสไล่เสือจากเคหา      รับหมาป่าเข้ามาเลยอาสัญ
  ฝ่ายอ้องอุ้นยุแยกให้แตกกัน          ใช้สาวนั้นเป็นชนวนชื่นชวนใจ
    พลันลิฉุยกุยกีกลับก่อเหตุ          ช่างอาเพศจริงหนาฟ้าร้องไห้
  ต้องรบราฆ่าฟันจนบรรลัย           ฤๅหาใครค้ำชูกู้บรรลังก์ ฯ

  (The above is a two-column text. If combining characters are handled
  correctly, the lines of the second column should be aligned with the
  | character above.)

Ethiopian:

  Proverbs in the Amharic language:

  ሰማይ አይታረስ ንጉሥ አይከሰስ።
  ብላ ካለኝ እንደአባቴ በቆመጠኝ።
  ጌጥ ያለቤቱ ቁምጥና ነው።
  ደሀ በሕልሙ ቅቤ ባይጠጣ ንጣት በገደለው።
  የአፍ ወለምታ በቅቤ አይታሽም።
  አይጥ በበላ ዳዋ ተመታ።
  ሲተረጉሙ ይደረግሙ።
  ቀስ በቀስ፥ ዕንቁላል በእግሩ ይሄዳል።
  ድር ቢያብር አንበሳ ያስር።
  ሰው እንደቤቱ እንጅ እንደ ጉረቤቱ አይተዳደርም።
  እግዜር የከፈተውን ጉሮሮ ሳይዘጋው አይድርም።
  የጎረቤት ሌባ፥ ቢያዩት ይስቅ ባያዩት ያጠልቅ።
  ሥራ ከመፍታት ልጄን ላፋታት።
  ዓባይ ማደሪያ የለው፥ ግንድ ይዞ ይዞራል።
  የእስላም አገሩ መካ የአሞራ አገሩ ዋርካ።
  ተንጋሎ ቢተፉ ተመልሶ ባፉ።
  ወዳጅህ ማር ቢሆን ጨርስህ አትላሰው።
  እግርህን በፍራሽህ ልክ ዘርጋ።

Runes:

  ᚻᛖ ᚳᚹᚫᚦ ᚦᚫᛏ ᚻᛖ ᛒᚢᛞᛖ ᚩᚾ ᚦᚫᛗ ᛚᚪᚾᛞᛖ ᚾᚩᚱᚦᚹᛖᚪᚱᛞᚢᛗ ᚹᛁᚦ ᚦᚪ ᚹᛖᛥᚫ

  (Old English, which transcribed into Latin reads 'He cwaeth that he
  bude thaem lande northweardum with tha Westsae.' and means 'He said
  that he lived in the northern land near the Western Sea.')

Braille:

  ⡌⠁⠧⠑ ⠼⠁⠒  ⡍⠜⠇⠑⠹⠰⠎ ⡣⠕⠌

  ⡍⠜⠇⠑⠹ ⠺⠁⠎ ⠙⠑⠁⠙⠒ ⠞⠕ ⠃⠑⠛⠔ ⠺⠊⠹⠲ ⡹⠻⠑ ⠊⠎ ⠝⠕ ⠙⠳⠃⠞
  ⠱⠁⠞⠑⠧⠻ ⠁⠃⠳⠞ ⠹⠁⠞⠲ ⡹⠑ ⠗⠑⠛⠊⠌⠻ ⠕⠋ ⠙⠊⠎ ⠃⠥⠗⠊⠁⠇ ⠺⠁⠎
  ⠎⠊⠛⠝⠫ ⠃⠹ ⠹⠑ ⠊⠇⠻⠛⠹⠍⠁⠝⠂ ⠹⠑ ⠊⠇⠻⠅⠂ ⠹⠑ ⠥⠝⠙⠻⠞⠁⠅⠻⠂
  ⠁⠝⠙ ⠹⠑ ⠡⠊⠑⠋ ⠍⠳⠗⠝⠻⠲ ⡎⠊⠗⠕⠕⠛⠑ ⠎⠊⠛⠝⠫ ⠊⠞⠲ ⡁⠝⠙
  ⡎⠊⠗⠕⠕⠛⠑⠰⠎ ⠝⠁⠍⠑ ⠺⠁⠎ ⠛⠕⠕⠙ ⠥⠏⠕⠝ ⠰⡡⠁⠝⠛⠑⠂ ⠋⠕⠗ ⠁⠝⠹⠹⠔⠛ ⠙⠑
  ⠡⠕⠎⠑ ⠞⠕ ⠏⠥⠞ ⠙⠊⠎ ⠙⠁⠝⠙ ⠞⠕⠲

  ⡕⠇⠙ ⡍⠜⠇⠑⠹ ⠺⠁⠎ ⠁⠎ ⠙⠑⠁⠙ ⠁⠎ ⠁ ⠙⠕⠕⠗⠤⠝⠁⠊⠇⠲

  ⡍⠔⠙⠖ ⡊ ⠙⠕⠝⠰⠞ ⠍⠑⠁⠝ ⠞⠕ ⠎⠁⠹ ⠹⠁⠞ ⡊ ⠅⠝⠪⠂ ⠕⠋ ⠍⠹
  ⠪⠝ ⠅⠝⠪⠇⠫⠛⠑⠂ ⠱⠁⠞ ⠹⠻⠑ ⠊⠎ ⠏⠜⠞⠊⠊⠥⠇⠜⠇⠹ ⠙⠑⠁⠙ ⠁⠃⠳⠞
  ⠁ ⠙⠕⠕⠗⠤⠝⠁⠊⠇⠲ ⡊ ⠍⠊⠣⠞ ⠙⠁⠧⠑ ⠃⠑⠲ ⠔⠊⠇⠔⠫⠂ ⠍⠹⠎⠑⠇⠋⠂ ⠞⠕
  ⠗⠑⠛⠜⠙ ⠁ ⠊⠕⠋⠋⠔⠤⠝⠁⠊⠇ ⠁⠎ ⠹⠑ ⠙⠑⠁⠙⠑⠌ ⠏⠊⠑⠊⠑ ⠕⠋ ⠊⠗⠕⠝⠍⠕⠝⠛⠻⠹
  ⠔ ⠹⠑ ⠞⠗⠁⠙⠑⠲ ⡃⠥⠞ ⠹⠑ ⠺⠊⠎⠙⠕⠍ ⠕⠋ ⠳⠗ ⠁⠝⠊⠑⠌⠕⠗⠎
  ⠊⠎ ⠔ ⠹⠑ ⠎⠊⠍⠊⠇⠑⠆ ⠁⠝⠙ ⠍⠹ ⠥⠝⠙⠁⠇⠇⠪⠫ ⠙⠁⠝⠙⠎
  ⠩⠁⠇⠇ ⠝⠕⠞ ⠙⠊⠌⠥⠗⠃ ⠊⠞⠂ ⠕⠗ ⠹⠑ ⡊⠳⠝⠞⠗⠹⠰⠎ ⠙⠕⠝⠑ ⠋⠕⠗⠲ ⡹⠳
  ⠺⠊⠇⠇ ⠹⠻⠑⠋⠕⠗⠑ ⠏⠻⠍⠊⠞ ⠍⠑ ⠞⠕ ⠗⠑⠏⠑⠁⠞⠂ ⠑⠍⠏⠙⠁⠞⠊⠊⠁⠇⠇⠹⠂ ⠹⠁⠞
  ⡍⠜⠇⠑⠹ ⠺⠁⠎ ⠁⠎ ⠙⠑⠁⠙ ⠁⠎ ⠁ ⠙⠕⠕⠗⠤⠝⠁⠊⠇⠲

  (The first couple of paragraphs of "A Christmas Carol" by Dickens)

Compact font selection example text:

  ABCDEFGHIJKLMNOPQRSTUVWXYZ /0123456789
  abcdefghijklmnopqrstuvwxyz £©µÀÆÖÞßéöÿ
  –—‘“”„†•…‰™œŠŸž€ ΑΒΓΔΩαβγδω АБВГДабвгд
  ∀∂∈ℝ∧∪≡∞ ↑↗↨↻⇣ ┐┼╔╘░►☺♀ ﬁ�⑀₂ἠḂӥẄɐː⍎אԱა

Greetings in various languages:

  Hello world, Καλημέρα κόσμε, コンニチハ

Box drawing alignment tests:                                          █
                                                                      ▉
  ╔══╦══╗  ┌──┬──┐  ╭──┬──╮  ╭──┬──╮  ┏━━┳━━┓  ┎┒┏┑   ╷  ╻ ┏┯┓ ┌┰┐    ▊ ╱╲╱╲╳╳╳
  ║┌─╨─┐║  │╔═╧═╗│  │╒═╪═╕│  │╓─╁─╖│  ┃┌─╂─┐┃  ┗╃╄┙  ╶┼╴╺╋╸┠┼┨ ┝╋┥    ▋ ╲╱╲╱╳╳╳
  ║│╲ ╱│║  │║   ║│  ││ │ ││  │║ ┃ ║│  ┃│ ╿ │┃  ┍╅╆┓   ╵  ╹ ┗┷┛ └┸┘    ▌ ╱╲╱╲╳╳╳
  ╠╡ ╳ ╞╣  ├╢   ╟┤  ├┼─┼─┼┤  ├╫─╂─╫┤  ┣┿╾┼╼┿┫  ┕┛┖┚     ┌┄┄┐ ╎ ┏┅┅┓ ┋ ▍ ╲╱╲╱╳╳╳
  ║│╱ ╲│║  │║   ║│  ││ │ ││  │║ ┃ ║│  ┃│ ╽ │┃  ░░▒▒▓▓██ ┊  ┆ ╎ ╏  ┇ ┋ ▎
  ║└─╥─┘║  │╚═╤═╝│  │╘═╪═╛│  │╙─╀─╜│  ┃└─╂─┘┃  ░░▒▒▓▓██ ┊  ┆ ╎ ╏  ┇ ┋ ▏
  ╚══╩══╝  └──┴──┘  ╰──┴──╯  ╰──┴──╯  ┗━━┻━━┛           └╌╌┘ ╎ ┗╍╍┛ ┋  ▁▂▃▄▅▆▇█

"""

class Test(unittest.TestCase):
    
    HOST = 'imap.host'
    PORT = 993
    USER = 'username'
    PASSWORD = 'password'
    
    def make_fs(self):
        """Return an FS instance.

        """
        return IMAPFS(host=self.HOST, port=self.PORT, user=self.USER, passwd=self.PASSWORD)

    def destroy_fs(self, fs):
        """Destroy a FS instance.

        Arguments:
            fs (FS): A filesystem instance previously opened
                by `~fs.test.FSTestCases.make_fs`.

        """
        fs.close()
        
    @property
    def TEST_DIR(self):
        return self.fs._delimiter.join(['INBOX', 'TEST'])
    
    @property
    def TEST_PATH(self):
        return '/'.join(['INBOX', 'TEST/'])

    def setUp(self):
        self.fs = self.make_fs()
        _delete_folder = []
        for _, _, name in self.fs.imap.list_folders():
            if name.startswith(self.TEST_DIR):
                _delete_folder.append(name)
        for folder in _delete_folder:
            self.fs.imap.delete_folder(folder)
        self.fs.makedir(self.TEST_PATH)

    def tearDown(self):
        self.destroy_fs(self.fs)
        del self.fs
        
    def assert_exists(self, path):
        """Assert a path exists.

        Arguments:
            path (str): A path on the filesystem.

        """
        self.assertTrue(self.fs.exists(path))

    def assert_not_exists(self, path):
        """Assert a path does not exist.

        Arguments:
            path (str): A path on the filesystem.

        """
        self.assertFalse(self.fs.exists(path))

    def assert_isfile(self, path):
        """Assert a path is a file.

        Arguments:
            path (str): A path on the filesystem.

        """
        self.assertTrue(self.fs.isfile(path))

    def assert_isdir(self, path):
        """Assert a path is a directory.

        Arguments:
            path (str): A path on the filesystem.

        """
        self.assertTrue(self.fs.isdir(path))

    def assert_bytes(self, path, contents):
        """Assert a file contains the given bytes.

        Arguments:
            path (str): A path on the filesystem.
            contents (bytes): Bytes to compare.

        """
        assert isinstance(contents, bytes)
        data = self.fs.getbytes(path)
        self.assertEqual(data, contents)
        self.assertIsInstance(data, bytes)

    def assert_text(self, path, contents):
        """Assert a file contains the given text.

        Arguments:
            path (str): A path on the filesystem.
            contents (str): Text to compare.

        """
        assert isinstance(contents, text_type)
        with self.fs.open(path, "rt") as f:
            data = f.read()
        self.assertEqual(data, contents)
        self.assertIsInstance(data, text_type)
        
    def test_root_dir(self):
        with self.assertRaises(errors.FileExpected):
            self.fs.open("/")
        with self.assertRaises(errors.FileExpected):
            self.fs.openbin("/")
            
    def test_appendbytes(self):
        with self.assertRaises(TypeError):
            self.fs.appendbytes(self.TEST_PATH + "1.eml", "bar")
        self.fs.appendbytes(self.TEST_PATH + "1.eml", b"bar\r\n")
        self.assert_bytes(self.TEST_PATH + "1.eml", b"bar\r\n")
        
        #IMAP file do not allow append
        with self.assertRaises(errors.FileExists):
            self.fs.appendbytes(self.TEST_PATH + "1.eml", b"baz\r\n")
        self.assert_bytes(self.TEST_PATH + "1.eml", b"bar\r\n")

    def test_appendtext(self):
        with self.assertRaises(TypeError):
            self.fs.appendtext(self.TEST_PATH + "1.eml", b"bar\r\n")
        self.fs.appendtext(self.TEST_PATH + "1.eml", "bar\r\n")
        self.assert_text(self.TEST_PATH + "1.eml", "bar\r\n")
        #IMAP file do not allow append
        with self.assertRaises(errors.FileExists):
            self.fs.appendtext(self.TEST_PATH + "1.eml", "baz\r\n")
        self.assert_text(self.TEST_PATH + "1.eml", "bar\r\n")

    def test_basic(self):
        #  Check str and repr don't break
        repr(self.fs)
        self.assertIsInstance(six.text_type(self.fs), six.text_type)
        
    def test_getmeta(self):
        # Get the meta dict
        meta = self.fs.getmeta()

        # Check default namespace
        self.assertEqual(meta, self.fs.getmeta(namespace="standard"))

        # Must be a dict
        self.assertTrue(isinstance(meta, dict))

        no_meta = self.fs.getmeta("__nosuchnamespace__")
        self.assertIsInstance(no_meta, dict)
        self.assertFalse(no_meta)
        
    def test_isfile(self):
        self.assertFalse(self.fs.isfile(self.TEST_PATH + "1.eml"))
        self.fs.create(self.TEST_PATH + "1.eml")
        self.assertTrue(self.fs.isfile(self.TEST_PATH + "1.eml"))
        self.fs.makedir(self.TEST_PATH + "bar")
        self.assertFalse(self.fs.isfile(self.TEST_PATH + "bar"))

    def test_isdir(self):
        self.assertFalse(self.fs.isdir(self.TEST_PATH + "foo"))
        self.fs.makedir(self.TEST_PATH + "foo")
        self.fs.create(self.TEST_PATH + "1.eml")
        self.assertTrue(self.fs.isdir(self.TEST_PATH + "foo"))
        self.assertFalse(self.fs.isdir(self.TEST_PATH + "1.eml"))

#     def test_islink(self):
#         self.fs.touch("foo")
#         self.assertFalse(self.fs.islink("foo"))
#         with self.assertRaises(errors.ResourceNotFound):
#             self.fs.islink("bar")

#     def test_getsize(self):
#         self.fs.setbytes("empty", b"")
#         self.fs.setbytes("one", b"a")
#         self.fs.setbytes("onethousand", ("b" * 1000).encode("ascii"))
#         self.assertEqual(self.fs.getsize("empty"), 0)
#         self.assertEqual(self.fs.getsize("one"), 1)
#         self.assertEqual(self.fs.getsize("onethousand"), 1000)
#         with self.assertRaises(errors.ResourceNotFound):
#             self.fs.getsize("doesnotexist")

#     def test_getsyspath(self):
#         self.fs.create("foo")
#         try:
#             syspath = self.fs.getsyspath("foo")
#         except errors.NoSysPath:
#             self.assertFalse(self.fs.hassyspath("foo"))
#         else:
#             self.assertIsInstance(syspath, text_type)
#             self.assertIsInstance(self.fs.getospath("foo"), bytes)
#             self.assertTrue(self.fs.hassyspath("foo"))
#         # Should not throw an error
#         self.fs.hassyspath("a/b/c/foo/bar")

#     def test_geturl(self):
#         self.fs.create("foo")
#         try:
#             self.fs.geturl("foo")
#         except errors.NoURL:
#             self.assertFalse(self.fs.hasurl("foo"))
#         else:
#             self.assertTrue(self.fs.hasurl("foo"))
#         # Should not throw an error
#         self.fs.hasurl("a/b/c/foo/bar")

#     def test_geturl_purpose(self):
#         """Check an unknown purpose raises a NoURL error.
#         """
#         self.fs.create("foo")
#         with self.assertRaises(errors.NoURL):
#             self.fs.geturl("foo", purpose="__nosuchpurpose__")

    def test_validatepath(self):
        """Check validatepath returns an absolute path.
        """
        path = self.fs.validatepath("foo")
        self.assertEqual(path, "/foo")

    def test_invalid_chars(self):
        # Test invalid path method.
        with self.assertRaises(errors.InvalidCharsInPath):
            self.fs.open("invalid\0file", "wb")
 
        with self.assertRaises(errors.InvalidCharsInPath):
            self.fs.validatepath("invalid\0file")

    def test_exists(self):
        # Test exists method.
        # Check root directory always exists
        self.assertTrue(self.fs.exists("/"))
        self.assertTrue(self.fs.exists(""))
 
        # Check files don't exist
        self.assertFalse(self.fs.exists(self.TEST_PATH + "foo"))
        self.assertFalse(self.fs.exists(self.TEST_PATH + "foo/bar"))
        self.assertFalse(self.fs.exists(self.TEST_PATH + "foo/bar/baz"))
        self.assertFalse(self.fs.exists(self.TEST_PATH + "egg"))
 
        # make some files and directories
        self.fs.makedirs(self.TEST_PATH + "foo/bar")
        self.fs.setbytes(self.TEST_PATH + "foo/bar/1.eml", b"test")
 
        # Check files exists
        self.assertTrue(self.fs.exists(self.TEST_PATH + "foo"))
        self.assertTrue(self.fs.exists(self.TEST_PATH + "foo/bar"))
        self.assertTrue(self.fs.exists(self.TEST_PATH + "foo/bar/1.eml"))
        self.assertFalse(self.fs.exists(self.TEST_PATH + "egg"))
 
        self.assert_exists(self.TEST_PATH + "foo")
        self.assert_exists(self.TEST_PATH + "foo/bar")
        self.assert_exists(self.TEST_PATH + "foo/bar/1.eml")
        self.assert_not_exists(self.TEST_PATH + "egg")
 
        # Delete a file
        self.fs.remove(self.TEST_PATH + "foo/bar/1.eml")
        # Check it no longer exists
        self.assert_not_exists(self.TEST_PATH + "foo/bar/1.eml")
        self.assertFalse(self.fs.exists(self.TEST_PATH + "foo/bar/1.eml"))
        self.assert_not_exists(self.TEST_PATH + "foo/bar/1.eml")
 
        # Check root directory always exists
        self.assertTrue(self.fs.exists("/"))
        self.assertTrue(self.fs.exists(""))

    def test_listdir(self):
        # Check listing directory that doesn't exist
        with self.assertRaises(errors.ResourceNotFound):
            self.fs.listdir("foobar")

        # Check aliases for root
        self.assertEqual(self.fs.listdir("/"), ['INBOX'])
        self.assertEqual(self.fs.listdir("."), ['INBOX'])
        self.assertEqual(self.fs.listdir("./"), ['INBOX'])

        # Make a few objects
        self.fs.makedir(self.TEST_PATH + "baz")
        
        # Check list works
        six.assertCountEqual(self, self.fs.listdir(self.TEST_PATH), ["baz"])
        
        
        self.fs.setbytes(self.TEST_PATH + "baz/1.eml", b"egg")
        self.fs.setbytes(self.TEST_PATH + "baz/2.eml", b"egg")
        self.fs.makedir(self.TEST_PATH + "baz/foo")
 
        # This should not be listed
        self.fs.setbytes(self.TEST_PATH + "baz/foo/1.eml", b"egg")
 
        # Check list works
        six.assertCountEqual(self, self.fs.listdir(self.TEST_PATH + "baz"), ["1.eml", "2.eml", "foo"])
 
        # Check paths are unicode strings
        for name in self.fs.listdir("/"):
            self.assertIsInstance(name, text_type)
 
        # Create a subdirectory
        self.fs.makedir(self.TEST_PATH + "dir")
 
        # Should start empty
        self.assertEqual(self.fs.listdir(self.TEST_PATH + "dir"), [])
 
        # Write some files
        self.fs.setbytes(self.TEST_PATH + "dir/1.eml", b"egg")
        self.fs.setbytes(self.TEST_PATH + "dir/2.eml", b"egg")
 
        # Check listing subdirectory
        six.assertCountEqual(self, self.fs.listdir(self.TEST_PATH + "dir"), ["1.eml", "2.eml"])
        # Make sure they are unicode stringd
        for name in self.fs.listdir(self.TEST_PATH + "dir"):
            self.assertIsInstance(name, text_type)
 
        self.fs.create(self.TEST_PATH + "dir/3.eml")
        with self.assertRaises(errors.DirectoryExpected):
            self.fs.listdir(self.TEST_PATH + "dir/3.eml")

#     def test_move(self):
#         # Make a file
#         self.fs.setbytes("foo", b"egg")
#         self.assert_isfile("foo")
# 
#         # Move it
#         self.fs.move("foo", "bar")
# 
#         # Check it has gone from original location
#         self.assert_not_exists("foo")
# 
#         # Check it exists in the new location, and contents match
#         self.assert_exists("bar")
#         self.assert_bytes("bar", b"egg")
# 
#         # Check moving to existing file fails
#         self.fs.setbytes("foo2", b"eggegg")
#         with self.assertRaises(errors.DestinationExists):
#             self.fs.move("foo2", "bar")
# 
#         # Check move with overwrite=True
#         self.fs.move("foo2", "bar", overwrite=True)
#         self.assert_not_exists("foo2")
# 
#         # Check moving to a non-existant directory
#         with self.assertRaises(errors.ResourceNotFound):
#             self.fs.move("bar", "egg/bar")
# 
#         # Check moving an unexisting source
#         with self.assertRaises(errors.ResourceNotFound):
#             self.fs.move("egg", "spam")
# 
#         # Check moving between different directories
#         self.fs.makedir("baz")
#         self.fs.setbytes("baz/bazbaz", b"bazbaz")
#         self.fs.makedir("baz2")
#         self.fs.move("baz/bazbaz", "baz2/bazbaz")
#         self.assert_not_exists("baz/bazbaz")
#         self.assert_bytes("baz2/bazbaz", b"bazbaz")
# 
#         # Check moving a directory raises an error
#         self.assert_isdir("baz2")
#         self.assert_not_exists("yolk")
#         with self.assertRaises(errors.FileExpected):
#             self.fs.move("baz2", "yolk")

    def test_makedir(self):
        # Check edge case of root
        with self.assertRaises(errors.DirectoryExists):
            self.fs.makedir("/")

        # Making root is a null op with recreate
        slash_fs = self.fs.makedir("/", recreate=True)
        self.assertIsInstance(slash_fs, SubFS)
        self.assertEqual(self.fs.listdir("/"), ['INBOX'])

        self.assert_not_exists(self.TEST_PATH + "foo")
        self.fs.makedir(self.TEST_PATH + "foo")
        self.assert_isdir(self.TEST_PATH + "foo")
        self.assertEqual(self.fs.gettype(self.TEST_PATH + "foo"), ResourceType.directory)
        self.fs.setbytes(self.TEST_PATH + "foo/1.eml", b"egg\r\n")
        self.assert_bytes(self.TEST_PATH + "foo/1.eml", b"egg\r\n")
 
        # Directory exists
        with self.assertRaises(errors.DirectoryExists):
            self.fs.makedir(self.TEST_PATH + "foo")
 
        # Parent directory doesn't exist
        with self.assertRaises(errors.ResourceNotFound):
            self.fs.makedir(self.TEST_PATH + "/foo/bar/baz")
 
        self.fs.makedir('/' + self.TEST_PATH + "foo/bar")
        self.fs.makedir('/' + self.TEST_PATH + "foo/bar/baz")
 
        with self.assertRaises(errors.DirectoryExists):
            self.fs.makedir(self.TEST_PATH + "foo/bar/baz")
 
        with self.assertRaises(errors.DirectoryExists):
            self.fs.makedir(self.TEST_PATH + "foo/1.eml")

    def test_makedirs(self):
        self.assertFalse(self.fs.exists(self.TEST_PATH + "foo"))
        self.fs.makedirs(self.TEST_PATH + "foo")
        self.assertEqual(self.fs.gettype(self.TEST_PATH + "foo"), ResourceType.directory)
 
        self.fs.makedirs(self.TEST_PATH + "foo/bar/baz")
        self.assertTrue(self.fs.isdir(self.TEST_PATH + "foo/bar"))
        self.assertTrue(self.fs.isdir(self.TEST_PATH + "foo/bar/baz"))
 
        with self.assertRaises(errors.DirectoryExists):
            self.fs.makedirs(self.TEST_PATH + "foo/bar/baz")
 
        self.fs.makedirs(self.TEST_PATH + "foo/bar/baz", recreate=True)
 
        self.fs.setbytes(self.TEST_PATH + "foo/1.eml", b"test\r\n")
        with self.assertRaises(errors.DirectoryExpected):
            self.fs.makedirs(self.TEST_PATH + "foo/1.eml/bar")
  
        with self.assertRaises(errors.DirectoryExpected):
            self.fs.makedirs(self.TEST_PATH + "foo/1.eml/bar/baz/egg")
 
    def test_repeat_dir(self):
        # Catches bug with directories contain repeated names,
        # discovered in s3fs
        self.fs.makedirs(self.TEST_PATH + "foo/foo/foo")
        self.assertEqual(self.fs.listdir(self.TEST_PATH), ["foo"])
        self.assertEqual(self.fs.listdir(self.TEST_PATH + "foo"), ["foo"])
        self.assertEqual(self.fs.listdir(self.TEST_PATH + "foo/foo"), ["foo"])
        self.assertEqual(self.fs.listdir(self.TEST_PATH + "foo/foo/foo"), [])
        scan = list(self.fs.scandir(self.TEST_PATH + "foo"))
        self.assertEqual(len(scan), 1)
        self.assertEqual(scan[0].name, "foo")
 
    def test_open(self):
        # Open a file that doesn't exist
        with self.assertRaises(errors.ResourceNotFound):
            self.fs.open(self.TEST_PATH + "doesnotexist", "r")
 
        self.fs.makedir(self.TEST_PATH + "foo")
 
        # Create a new text file
        text = "Hello, World\r\n"
 
        with self.fs.open(self.TEST_PATH + "foo/1.eml", "wt") as f:
            repr(f)
            self.assertIsInstance(f, io.IOBase)
            self.assertTrue(f.writable())
            self.assertFalse(f.readable())
            self.assertFalse(f.closed)
            f.write(text)
        self.assertTrue(f.closed)
 
        # Read it back
        with self.fs.open(self.TEST_PATH + "foo/1.eml", "rt") as f:
            self.assertIsInstance(f, io.IOBase)
            self.assertTrue(f.readable())
            self.assertFalse(f.writable())
            self.assertFalse(f.closed)
            hello = f.read()
        self.assertTrue(f.closed)
        self.assertEqual(hello, text)
        self.assert_text(self.TEST_PATH + "foo/1.eml", text)
 
        # Test overwrite
        text = "Goodbye, World"
        #Imap file cannot be overwritten
        with self.assertRaises(errors.FileExists):
            with self.fs.open(self.TEST_PATH + "foo/1.eml", "wt") as f:
                pass
 
        # Open from missing dir
        with self.assertRaises(errors.ResourceNotFound):
            self.fs.open(self.TEST_PATH + "foo/bar/1.eml")
 
        # Test fileno returns a file number, if supported by the file.
        with self.fs.open(self.TEST_PATH + "foo/1.eml") as f:
            try:
                fn = f.fileno()
            except io.UnsupportedOperation:
                pass
            else:
                self.assertEqual(os.read(fn, 7), b"Goodbye")
 
        # Test text files are proper iterators over themselves
        lines = "\r\n".join(["Line 1", "Line 2", "Line 3\r\n"])
        self.fs.settext(self.TEST_PATH + "foo/2.eml", lines)
        with self.fs.open(self.TEST_PATH + "foo/2.eml") as f:
            for actual, expected in zip(f, lines.splitlines(1)):
                self.assertEqual(actual, expected)
 
    def test_openbin_rw(self):
        # Open a file that doesn't exist
        with self.assertRaises(errors.ResourceNotFound):
            self.fs.openbin(self.TEST_PATH + "doesnotexist", "r")
 
        self.fs.makedir(self.TEST_PATH + "foo")
 
        # Create a new text file
        text = b"Hello, World\r\n"
        
        with self.assertRaises(errors.PathError):
            self.fs.openbin(self.TEST_PATH + "foo/1", "w")
 
        with self.fs.openbin(self.TEST_PATH + "foo/1.eml", "w") as f:
            repr(f)
            self.assertIsInstance(f, io.IOBase)
            self.assertTrue(f.writable())
            self.assertFalse(f.readable())
            self.assertEqual(len(text), f.write(text))
            self.assertFalse(f.closed)
        self.assertTrue(f.closed)
 
        with self.assertRaises(errors.FileExists):
            with self.fs.openbin(self.TEST_PATH + "foo/1.eml", "x") as f:
                pass
 
        # Read it back
        with self.fs.openbin(self.TEST_PATH + "foo/1.eml", "r") as f:
            self.assertIsInstance(f, io.IOBase)
            self.assertTrue(f.readable())
            self.assertFalse(f.writable())
            hello = f.read()
            self.assertFalse(f.closed)
        self.assertTrue(f.closed)
        self.assertEqual(hello, text)
        self.assert_bytes(self.TEST_PATH + "foo/1.eml", text)
 
        # Test overwrite
        text = b"Goodbye, World"
        #Imap file cannot be overwritten
        with self.assertRaises(errors.FileExists):
            with self.fs.openbin(self.TEST_PATH + "foo/1.eml", "w") as f:
                self.assertEqual(len(text), f.write(text))
 
        # Test FileExpected raised
        with self.assertRaises(errors.FileExpected):
            self.fs.openbin(self.TEST_PATH + "foo")  # directory

        # Open from missing dir
        with self.assertRaises(errors.ResourceNotFound):
            self.fs.openbin('/' + self.TEST_PATH + "foo/bar/test.txt")
 
        # Test fileno returns a file number, if supported by the file.
        with self.fs.openbin(self.TEST_PATH + "foo/1.eml") as f:
            try:
                fn = f.fileno()
            except io.UnsupportedOperation:
                pass
            else:
                self.assertEqual(os.read(fn, 7), b"Goodbye")
 
        # Test binary files are proper iterators over themselves
        lines = b"\r\n".join([b"Line 1", b"Line 2", b"Line 3\r\n"])
        self.fs.setbytes(self.TEST_PATH + "foo/2.eml", lines)
        with self.fs.openbin(self.TEST_PATH + "foo/2.eml") as f:
            for actual, expected in zip(f, lines.splitlines(1)):
                self.assertEqual(actual, expected)
 
    def test_open_files(self):
        # Test file-like objects work as expected.
        
        with self.fs.open(self.TEST_PATH + "1.eml", "w") as f:
            repr(f)
            text_type(f)
            self.assertIsInstance(f, io.IOBase)
            self.assertTrue(f.writable())
            self.assertFalse(f.readable())
            self.assertFalse(f.closed)
            self.assertEqual(f.tell(), 0)
            f.write("Hello\r\nWorld\r\n")
            self.assertEqual(f.tell(), 14)
            f.writelines(["foo\r\n", "bar\r\n", "baz\r\n"])
            with self.assertRaises(IOError):
                f.read(1)
        self.assertTrue(f.closed)
 
        with self.fs.open(self.TEST_PATH + "2.eml", "wb") as f:
            with self.assertRaises(IOError):
                f.read(1)
 
        with self.fs.open(self.TEST_PATH + "1.eml", "r") as f:
            repr(f)
            text_type(f)
            self.assertIsInstance(f, io.IOBase)
            self.assertFalse(f.writable())
            self.assertTrue(f.readable())
            self.assertFalse(f.closed)
            self.assertEqual(
                f.readlines(), ["Hello\r\n", "World\r\n", "foo\r\n", "bar\r\n", "baz\r\n"]
            )
            with self.assertRaises(IOError):
                f.write("no")
        self.assertTrue(f.closed)
 
        with self.fs.open(self.TEST_PATH + "1.eml", "rb") as f:
            self.assertIsInstance(f, io.IOBase)
            self.assertFalse(f.writable())
            self.assertTrue(f.readable())
            self.assertFalse(f.closed)
            self.assertEqual(f.readlines(8), [b"Hello\r\n", b"World\r\n"])
            with self.assertRaises(IOError):
                f.write(b"no")
        self.assertTrue(f.closed)
 
        with self.fs.open(self.TEST_PATH + "1.eml", "r", encoding='ascii') as f:
            self.assertEqual(list(f), ['Hello\r\n', 'World\r\n', 'foo\r\n', 'bar\r\n', 'baz\r\n'])
            self.assertFalse(f.closed)
        self.assertTrue(f.closed)
 
        iter_lines = iter(self.fs.open(self.TEST_PATH + "1.eml"))
        self.assertEqual(next(iter_lines), "Hello\r\n")
 
        #unicode
        with self.fs.open(self.TEST_PATH + "3.eml", "w") as f:
            self.assertEqual(14, f.write("Héllo\r\nWörld\r\n"))
 
        with self.fs.open(self.TEST_PATH + "3.eml", "rb") as f:
            self.assertIsInstance(f, io.IOBase)
            self.assertFalse(f.writable())
            self.assertTrue(f.readable())
            self.assertTrue(f.seekable())
            self.assertFalse(f.closed)
            self.assertEqual(f.read(1), b"H")
            self.assertEqual(3, f.seek(3, Seek.set))
            self.assertEqual(f.read(1), b"l")
            self.assertEqual(8, f.seek(4, Seek.current))
            self.assertEqual(f.read(1), b"W")
            self.assertEqual(14, f.seek(-2, Seek.end))
            self.assertEqual(f.read(1), b"\r")
            with self.assertRaises(ValueError):
                f.seek(10, 77)
        self.assertTrue(f.closed)
        
        with self.assertRaises(errors.FileExists):
            with self.fs.open(self.TEST_PATH + "3.eml", "r+b") as f:
                pass
                self.assertIsInstance(f, io.IOBase)
 
    def test_openbin(self):
        # Write a binary file
        with self.fs.openbin(self.TEST_PATH + "1.eml", "wb") as write_file:
            repr(write_file)
            text_type(write_file)
            self.assertIsInstance(write_file, io.IOBase)
            self.assertTrue(write_file.writable())
            self.assertFalse(write_file.readable())
            self.assertFalse(write_file.closed)
            self.assertEqual(5, write_file.write(b"\1\2\3\r\n"))
        self.assertTrue(write_file.closed)
 
        # Read a binary file
        with self.fs.openbin(self.TEST_PATH + "1.eml", "rb") as read_file:
            repr(write_file)
            text_type(write_file)
            self.assertIsInstance(read_file, io.IOBase)
            self.assertTrue(read_file.readable())
            self.assertFalse(read_file.writable())
            self.assertFalse(read_file.closed)
            data = read_file.read()
        self.assertEqual(data, b"\1\2\3\r\n")
        self.assertTrue(read_file.closed)
 
        # Check disallow text mode
        with self.assertRaises(ValueError):
            with self.fs.openbin(self.TEST_PATH + "1.eml", "rt") as read_file:
                pass
 
        # Check errors
        with self.assertRaises(errors.ResourceNotFound):
            self.fs.openbin(self.TEST_PATH + "2.eml")
 
        # Open from missing dir
        with self.assertRaises(errors.ResourceNotFound):
            self.fs.openbin('/' + self.TEST_PATH + "bar/test.txt")
 
        # Attempt to open a directory
        with self.assertRaises(errors.FileExpected):
            self.fs.openbin('/' + self.TEST_PATH)
 
        # Attempt to write to a directory
        with self.assertRaises(errors.FileExpected):
            self.fs.openbin("/" + self.TEST_PATH, "w")
 
        # Opening a file in a directory which doesn't exist
        with self.assertRaises(errors.ResourceNotFound):
            self.fs.openbin(self.TEST_PATH + "egg/1.eml")
 
        # Opening a file in a directory which doesn't exist
        with self.assertRaises(errors.ResourceNotFound):
            self.fs.openbin(self.TEST_PATH + "egg/1.eml", "w")
 
        # Opening with a invalid mode
        with self.assertRaises(ValueError):
            self.fs.openbin(self.TEST_PATH + "1.eml", "h")
 
    def test_open_exclusive(self):
        with self.fs.open(self.TEST_PATH + "1.eml", "x") as f:
            f.write("bananas")
 
        with self.assertRaises(errors.FileExists):
            self.fs.open(self.TEST_PATH + "1.eml", "x")
 
    def test_openbin_exclusive(self):
        with self.fs.openbin(self.TEST_PATH + "1.eml", "x") as f:
            f.write(b"bananas")
 
        with self.assertRaises(errors.FileExists):
            self.fs.openbin(self.TEST_PATH + "1.eml", "x")
 
    def test_opendir(self):
        # Make a simple directory structure
        self.fs.setbytes(self.TEST_PATH + "1.eml", b"barbar\r\n")
        self.fs.setbytes(self.TEST_PATH + "2.eml", b"eggegg\r\n")
 
        # Open a sub directory
        with self.fs.opendir(self.TEST_PATH) as foo_fs:
            repr(foo_fs)
            text_type(foo_fs)
            six.assertCountEqual(self, foo_fs.listdir('/'), ["1.eml", "2.eml"])
            self.assertTrue(foo_fs.isfile("1.eml"))
            self.assertTrue(foo_fs.isfile("2.eml"))
            self.assertEqual(foo_fs.getbytes("1.eml"), b"barbar\r\n")
            self.assertEqual(foo_fs.getbytes("2.eml"), b"eggegg\r\n")
 
        self.assertFalse(self.fs.isclosed())
 
        # Attempt to open a non-existent directory
        with self.assertRaises(errors.ResourceNotFound):
            self.fs.opendir(self.TEST_PATH + "egg")
 
        # Check error when doing opendir on a non dir
        with self.assertRaises(errors.DirectoryExpected):
            self.fs.opendir(self.TEST_PATH + "1.eml")
 
        # These should work, and will essentially return a 'clone' of sorts
        self.fs.opendir("")
        self.fs.opendir("/")
 
        # Check ClosingSubFS closes 'parent'
        with self.fs.opendir(self.TEST_PATH, factory=ClosingSubFS) as foo_fs:
            six.assertCountEqual(self, foo_fs.listdir("/"), ["1.eml", "2.eml"])
            self.assertTrue(foo_fs.isfile("1.eml"))
            self.assertTrue(foo_fs.isfile("2.eml"))
            self.assertEqual(foo_fs.getbytes("1.eml"), b"barbar\r\n")
            self.assertEqual(foo_fs.getbytes("2.eml"), b"eggegg\r\n")
 
        self.assertTrue(self.fs.isclosed())
 
    def test_remove(self):
        self.fs.setbytes(self.TEST_PATH + "1.eml", b"test1")
        self.fs.setbytes(self.TEST_PATH + "2.eml", b"test2")
        self.fs.setbytes(self.TEST_PATH + "3.eml", b"test3")
 
        self.assert_isfile(self.TEST_PATH + "1.eml")
        self.assert_isfile(self.TEST_PATH + "2.eml")
        self.assert_isfile(self.TEST_PATH + "3.eml")
 
        self.fs.remove(self.TEST_PATH + "2.eml")
 
        self.assert_isfile(self.TEST_PATH + "1.eml")
        self.assert_not_exists(self.TEST_PATH + "2.eml")
        self.assert_isfile(self.TEST_PATH + "3.eml")
 
        with self.assertRaises(errors.ResourceNotFound):
            self.fs.remove("bar")
 
        self.fs.makedir(self.TEST_PATH + "dir")
        with self.assertRaises(errors.FileExpected):
            self.fs.remove(self.TEST_PATH + "dir")
 
        self.fs.makedirs(self.TEST_PATH + "foo/bar/baz/")
 
        error_msg = "resource '%sfoo/bar/egg/test.txt' not found" % self.TEST_PATH
        with self.assertRaisesRegexp(errors.ResourceNotFound, error_msg):
            self.fs.remove(self.TEST_PATH + "foo/bar/egg/test.txt")
 
    def test_removedir(self):
 
        # Test removing root
        with self.assertRaises(errors.RemoveRootError):
            self.fs.removedir("/")
 
        self.fs.makedirs(self.TEST_PATH + "foo/bar/baz")
        self.assertTrue(self.fs.exists(self.TEST_PATH + "foo/bar/baz"))
        self.fs.removedir(self.TEST_PATH + "foo/bar/baz")
        self.assertFalse(self.fs.exists(self.TEST_PATH + "foo/bar/baz"))
        self.assertTrue(self.fs.isdir(self.TEST_PATH + "foo/bar"))
 
        with self.assertRaises(errors.ResourceNotFound):
            self.fs.removedir(self.TEST_PATH + "nodir")
 
        # Test force removal
        self.fs.makedirs(self.TEST_PATH + "foo/bar/baz")
        self.fs.setbytes(self.TEST_PATH + "foo/1.eml", b"test")
 
        with self.assertRaises(errors.DirectoryExpected):
            self.fs.removedir(self.TEST_PATH + "foo/1.eml")
 
        with self.assertRaises(errors.DirectoryNotEmpty):
            self.fs.removedir(self.TEST_PATH + "foo/bar")

    def test_removetree(self):
        self.fs.makedirs(self.TEST_PATH + "foo/bar/baz")
        self.fs.makedirs(self.TEST_PATH + "foo/egg")
        self.fs.makedirs(self.TEST_PATH + "foo/a/b/c/d/e")
        self.fs.create(self.TEST_PATH + "foo/1.eml")
        self.fs.create(self.TEST_PATH + "foo/bar/1.eml")
        self.fs.create(self.TEST_PATH + "foo/bar/baz/1.eml")
        self.fs.create(self.TEST_PATH + "foo/a/b/c/1.eml")
        self.fs.create(self.TEST_PATH + "foo/a/b/c/2.eml")
        self.fs.create(self.TEST_PATH + "foo/a/b/c/3.eml")
 
        self.assert_exists(self.TEST_PATH + "foo/1.eml")
        self.assert_exists(self.TEST_PATH + "foo/bar/1.eml")
 
        self.fs.removetree(self.TEST_PATH + "foo")
        self.assert_not_exists(self.TEST_PATH + "foo")
        
    def test_getinfo(self):
        # Test special case of root directory
        # Root directory has a name of ''
        root_info = self.fs.getinfo("/")
        self.assertEqual(root_info.name, "")
        self.assertTrue(root_info.is_dir)
        
        # Make a file of known size
        self.fs.setbytes(self.TEST_PATH + "1.eml", b"bar\r\n")
        self.fs.makedir(self.TEST_PATH + "dir")

        # Check basic namespace
        info = self.fs.getinfo(self.TEST_PATH + "1.eml").raw
        self.assertIsInstance(info["basic"]["name"], text_type)
        self.assertEqual(info["basic"]["name"], "1.eml")
        self.assertFalse(info["basic"]["is_dir"])

        # Check basic namespace dir
        info = self.fs.getinfo(self.TEST_PATH + "dir").raw
        self.assertEqual(info["basic"]["name"], "dir")
        self.assertTrue(info["basic"]["is_dir"])

        # Get the info
        info = self.fs.getinfo(self.TEST_PATH + "1.eml", namespaces=["details"]).raw
        self.assertIsInstance(info, dict)
        self.assertEqual(info["details"]["size"], 5)
        self.assertEqual(info["details"]["type"], int(ResourceType.file))

        # Test getdetails
        self.assertEqual(info, self.fs.getdetails(self.TEST_PATH + "1.eml").raw)

        # Raw info should be serializable
        try:
            json.dumps(info)
        except:
            assert False, "info should be JSON serializable"

        # Non existant namespace is not an error
        no_info = self.fs.getinfo(self.TEST_PATH + "1.eml", "__nosuchnamespace__").raw
        self.assertIsInstance(no_info, dict)
        self.assertEqual(no_info["basic"], {"name": "1.eml", "is_dir": False})

        # Check a number of standard namespaces
        # FS objects may not support all these, but we can at least
        # invoke the code
        info = self.fs.getinfo(self.TEST_PATH + "1.eml", namespaces=["access", "stat", "details"])

        # Check that if the details namespace is present, times are
        # of valid types.
        if 'details' in info.namespaces:
            details = info.raw['details']
            self.assertIsInstance(details.get('accessed'), (type(None), int, float))
            self.assertIsInstance(details.get('modified'), (type(None), int, float))
            self.assertIsInstance(details.get('created'), (type(None), int, float))
            self.assertIsInstance(details.get('metadata_changed'), (type(None), int, float))

    def test_getinfo_IMAP(self):
        # Make a file of known size
        self.fs.setbytes(self.TEST_PATH + "1.eml", b"bar\r\n")
        self.fs.makedir(self.TEST_PATH + "dir")
        
        # Check IMAP namespace dir
        info = self.fs.getinfo(self.TEST_PATH + "dir")
        self.assertTrue('imap' in info.namespaces)
        self.assertIsInstance(info.get('imap', 'flags'), list)
        self.assertEqual(info.get('imap', 'messages'), 0)
        self.assertIsInstance(info.get('imap', 'recent'), int)
        self.assertEqual(info.get('imap', 'uidnext'), 1)
        self.assertIsInstance(info.get('imap', 'uidvalidity'), int)
        self.assertEqual(info.get('imap', 'unseen'), 0)
        
        # Check IMAP namespace dir afer one mail added
        self.fs.setbytes(self.TEST_PATH + "dir/1.eml", b"bar\r\n")
        info = self.fs.getinfo(self.TEST_PATH + "dir")
        self.assertTrue('imap' in info.namespaces)
        self.assertIsInstance(info.get('imap', 'flags'), list)
        self.assertEqual(info.get('imap', 'messages'), 1)
        self.assertIsInstance(info.get('imap', 'recent'), int)
        self.assertEqual(info.get('imap', 'uidnext'), 2)
        self.assertIsInstance(info.get('imap', 'uidvalidity'), int)
        self.assertEqual(info.get('imap', 'unseen'), 1)
        
 
    def test_setinfo(self):
        self.fs.setbytes(self.TEST_PATH + "1.eml", b"bar\r\n")
        
        old_info = self.fs.getinfo(self.TEST_PATH + "1.eml").raw
        self.assertTrue('\\Seen' not in old_info['imap']['flags'])
 
        change_info = {'imap' : {'flags' : ['\\Seen']}}
        self.fs.setinfo(self.TEST_PATH + "1.eml", change_info)
        new_info = self.fs.getinfo(self.TEST_PATH + "1.eml", namespaces=["details"]).raw
        self.assertTrue('\\Seen' in new_info['imap']['flags'])
        
        with self.assertRaises(errors.ResourceNotFound):
            self.fs.setinfo("nothing", {})
            
        with self.assertRaises(errors.FileExpected):
            self.fs.setinfo(self.TEST_PATH, change_info)
            
# 
#     def test_settimes(self):
#         self.fs.create("birthday.txt")
#         self.fs.settimes("birthday.txt", accessed=datetime(2016, 7, 5))
#         old_info = self.fs.getinfo("birthday.txt", namespaces=["details"])
#         writeable = old_info.get("details", "_write", [])
#         if "accessed" in writeable:
#             self.assertEqual(old_info.accessed, datetime(2016, 7, 5, tzinfo=pytz.UTC))
#         if "modified" in writeable:
#             self.assertEqual(old_info.modified, datetime(2016, 7, 5, tzinfo=pytz.UTC))
# 
#     def test_touch(self):
#         self.fs.touch("new.txt")
#         self.assert_isfile("new.txt")
#         self.fs.settimes("new.txt", datetime(2016, 7, 5))
#         old_info = self.fs.getinfo("new.txt", namespaces=["details"])
#         if old_info.is_writeable("details", "accessed"):
#             self.assertEqual(old_info.accessed, datetime(2016, 7, 5, tzinfo=pytz.UTC))
#             now = time.time()
#             self.fs.touch("new.txt")
#             accessed = self.fs.getinfo("new.txt", namespaces=["details"]).raw[
#                 "details"
#             ]["accessed"]
#             self.assertTrue(accessed - now < 5)
# 
    def test_close(self):
        self.assertFalse(self.fs.isclosed())
        self.fs.close()
        self.assertTrue(self.fs.isclosed())
        # Check second close call is a no-op
        self.fs.close()
        self.assertTrue(self.fs.isclosed())
 
        # Check further operations raise a FilesystemClosed exception
        with self.assertRaises(errors.FilesystemClosed):
            self.fs.openbin("test.bin")
 
    def test_copy(self):
        # Test copy to new path
        self.fs.setbytes(self.TEST_PATH + "1.eml", b"test\r\n")
        self.fs.copy(self.TEST_PATH + "1.eml", self.TEST_PATH + "2.eml")
        self.assert_bytes(self.TEST_PATH + "2.eml", b"test\r\n")
 
        # Test copy over existing path
        self.fs.setbytes(self.TEST_PATH + "3.eml", b"truncateme\r\n")
        with self.assertRaises(errors.FileExists):
            self.fs.copy(self.TEST_PATH + "1.eml", self.TEST_PATH + "3.eml", overwrite=True)
        self.assert_bytes(self.TEST_PATH + "3.eml", b"truncateme\r\n")
  
        # Test copying a file to a destination that exists
        with self.assertRaises(errors.DestinationExists):
            self.fs.copy(self.TEST_PATH + "3.eml", self.TEST_PATH + "1.eml")
   
        # Test copying to a directory that doesn't exist
        with self.assertRaises(errors.ResourceNotFound):
            self.fs.copy(self.TEST_PATH + "3.eml", "a/b/c/3.eml")
  
        # Test copying a source that doesn't exist
        with self.assertRaises(errors.ResourceNotFound):
            self.fs.copy(self.TEST_PATH + "4.eml", self.TEST_PATH + "5.eml")
  
        # Test copying a directory
        self.fs.makedir(self.TEST_PATH + "dir")
        with self.assertRaises(errors.FileExpected):
            self.fs.copy(self.TEST_PATH + "dir", "folder")
# 
#     def _test_upload(self, workers):
#         """Test fs.copy with varying number of worker threads."""
#         data1 = b"foo" * 256 * 1024
#         data2 = b"bar" * 2 * 256 * 1024
#         data3 = b"baz" * 3 * 256 * 1024
#         data4 = b"egg" * 7 * 256 * 1024
# 
#         with open_fs("temp://") as src_fs:
#             src_fs.setbytes("foo", data1)
#             src_fs.setbytes("bar", data2)
#             src_fs.makedir("dir1").setbytes("baz", data3)
#             src_fs.makedirs("dir2/dir3").setbytes("egg", data4)
#             dst_fs = self.fs
#             fs.copy.copy_fs(src_fs, dst_fs, workers=workers)
#             self.assertEqual(dst_fs.getbytes("foo"), data1)
#             self.assertEqual(dst_fs.getbytes("bar"), data2)
#             self.assertEqual(dst_fs.getbytes("dir1/baz"), data3)
#             self.assertEqual(dst_fs.getbytes("dir2/dir3/egg"), data4)
# 
#     def test_upload_0(self):
#         self._test_upload(0)
# 
#     def test_upload_1(self):
#         self._test_upload(1)
# 
#     def test_upload_2(self):
#         self._test_upload(2)
# 
#     def test_upload_4(self):
#         self._test_upload(4)
# 
#     def _test_download(self, workers):
#         """Test fs.copy with varying number of worker threads."""
#         data1 = b"foo" * 256 * 1024
#         data2 = b"bar" * 2 * 256 * 1024
#         data3 = b"baz" * 3 * 256 * 1024
#         data4 = b"egg" * 7 * 256 * 1024
#         src_fs = self.fs
#         with open_fs("temp://") as dst_fs:
#             src_fs.setbytes("foo", data1)
#             src_fs.setbytes("bar", data2)
#             src_fs.makedir("dir1").setbytes("baz", data3)
#             src_fs.makedirs("dir2/dir3").setbytes("egg", data4)
#             fs.copy.copy_fs(src_fs, dst_fs, workers=workers)
#             self.assertEqual(dst_fs.getbytes("foo"), data1)
#             self.assertEqual(dst_fs.getbytes("bar"), data2)
#             self.assertEqual(dst_fs.getbytes("dir1/baz"), data3)
#             self.assertEqual(dst_fs.getbytes("dir2/dir3/egg"), data4)
# 
#     def test_download_0(self):
#         self._test_download(0)
# 
#     def test_download_1(self):
#         self._test_download(1)
# 
#     def test_download_2(self):
#         self._test_download(2)
# 
#     def test_download_4(self):
#         self._test_download(4)
# 
    def test_create(self):
        # Test create new file
        self.assertFalse(self.fs.exists(self.TEST_PATH + "foo"))
        self.fs.makedir(self.TEST_PATH + "foo")
        self.assertTrue(self.fs.exists(self.TEST_PATH + "foo"))
        
        self.assertFalse(self.fs.exists(self.TEST_PATH + "foo/1.eml"))
        self.fs.create(self.TEST_PATH + "foo/1.eml")
        self.assertTrue(self.fs.exists(self.TEST_PATH + "foo/1.eml"))
        self.assertEqual(self.fs.gettype(self.TEST_PATH + "foo/1.eml"), ResourceType.file)
        self.assertEqual(self.fs.getsize(self.TEST_PATH + "foo/1.eml"), 2)
  
        # Test wipe existing file
        with self.assertRaises(errors.FileExists):
            self.fs.setbytes(self.TEST_PATH + "foo/1.eml", b"bar")
        self.assertEqual(self.fs.getsize(self.TEST_PATH + "foo/1.eml"), 2)
        with self.assertRaises(errors.FileExists):
            self.fs.create(self.TEST_PATH + "foo/1.eml", wipe=True)
        self.assertEqual(self.fs.getsize(self.TEST_PATH + "foo/1.eml"), 2)
  
        # Test create with existing file, and not wipe
        with self.assertRaises(errors.FileExists):
            self.fs.setbytes(self.TEST_PATH + "foo/1.eml", b"bar")
        self.assertEqual(self.fs.getsize(self.TEST_PATH + "foo/1.eml"), 2)
#         with self.assertRaises(errors.FileExists):
        self.fs.create(self.TEST_PATH + "foo/1.eml", wipe=False)
        self.assertEqual(self.fs.getsize(self.TEST_PATH + "foo/1.eml"), 2)
# 
#     def test_desc(self):
#         # Describe a file
#         self.fs.create("foo")
#         description = self.fs.desc("foo")
#         self.assertIsInstance(description, text_type)
# 
#         # Describe a dir
#         self.fs.makedir("dir")
#         self.fs.desc("dir")
# 
#         # Special cases that may hide bugs
#         self.fs.desc("/")
#         self.fs.desc("")
# 
#         with self.assertRaises(errors.ResourceNotFound):
#             self.fs.desc("bar")
# 
#     def test_scandir(self):
#         # Check exception for scanning dir that doesn't exist
#         with self.assertRaises(errors.ResourceNotFound):
#             for info in self.fs.scandir("/foobar"):
#                 pass
# 
#         # Check scandir returns an iterable
#         iter_scandir = self.fs.scandir("/")
#         self.assertTrue(isinstance(iter_scandir, collections.Iterable))
#         self.assertEqual(list(iter_scandir), [])
# 
#         # Check scanning
#         self.fs.create("foo")
# 
#         # Can't scandir on a file
#         with self.assertRaises(errors.DirectoryExpected):
#             list(self.fs.scandir("foo"))
# 
#         self.fs.create("bar")
#         self.fs.makedir("dir")
#         iter_scandir = self.fs.scandir("/")
#         self.assertTrue(isinstance(iter_scandir, collections.Iterable))
# 
#         scandir = sorted(
#             [r.raw for r in iter_scandir], key=lambda info: info["basic"]["name"]
#         )
# 
#         # Filesystems may send us more than we ask for
#         # We just want to test the 'basic' namespace
#         scandir = [{"basic": i["basic"]} for i in scandir]
# 
#         self.assertEqual(
#             scandir,
#             [
#                 {"basic": {"name": "bar", "is_dir": False}},
#                 {"basic": {"name": "dir", "is_dir": True}},
#                 {"basic": {"name": "foo", "is_dir": False}},
#             ],
#         )
# 
#         # Hard to test optional namespaces, but at least run the code
#         list(
#             self.fs.scandir(
#                 "/", namespaces=["details", "link", "stat", "lstat", "access"]
#             )
#         )
# 
#         # Test paging
#         page1 = list(self.fs.scandir("/", page=(None, 2)))
#         self.assertEqual(len(page1), 2)
#         page2 = list(self.fs.scandir("/", page=(2, 4)))
#         self.assertEqual(len(page2), 1)
#         page3 = list(self.fs.scandir("/", page=(4, 6)))
#         self.assertEqual(len(page3), 0)
#         paged = set(r.name for r in itertools.chain(page1, page2))
#         self.assertEqual(paged, {"foo", "bar", "dir"})
# 
#     def test_filterdir(self):
#         self.assertEqual(list(self.fs.filterdir("/", files=["*.py"])), [])
# 
#         self.fs.makedir("bar")
#         self.fs.create("foo.txt")
#         self.fs.create("foo.py")
#         self.fs.create("foo.pyc")
# 
#         page1 = list(self.fs.filterdir("/", page=(None, 2)))
#         page2 = list(self.fs.filterdir("/", page=(2, 4)))
#         page3 = list(self.fs.filterdir("/", page=(4, 6)))
# 
#         self.assertEqual(len(page1), 2)
#         self.assertEqual(len(page2), 2)
#         self.assertEqual(len(page3), 0)
#         names = [info.name for info in itertools.chain(page1, page2, page3)]
#         self.assertEqual(set(names), {"foo.txt", "foo.py", "foo.pyc", "bar"})
# 
#         # Check filtering by wildcard
#         dir_list = [info.name for info in self.fs.filterdir("/", files=["*.py"])]
#         self.assertEqual(set(dir_list), {"bar", "foo.py"})
# 
#         # Check filtering by miltiple wildcard
#         dir_list = [
#             info.name for info in self.fs.filterdir("/", files=["*.py", "*.pyc"])
#         ]
#         self.assertEqual(set(dir_list), {"bar", "foo.py", "foo.pyc"})
# 
#         # Check excluding dirs
#         dir_list = [
#             info.name
#             for info in self.fs.filterdir(
#                 "/", exclude_dirs=["*"], files=["*.py", "*.pyc"]
#             )
#         ]
#         self.assertEqual(set(dir_list), {"foo.py", "foo.pyc"})
# 
#         # Check excluding files
#         dir_list = [info.name for info in self.fs.filterdir("/", exclude_files=["*"])]
#         self.assertEqual(set(dir_list), {"bar"})
# 
#         # Check wildcards must be a list
#         with self.assertRaises(TypeError):
#             dir_list = [info.name for info in self.fs.filterdir("/", files="*.py")]
# 
#         self.fs.makedir("baz")
#         dir_list = [
#             info.name
#             for info in self.fs.filterdir("/", exclude_files=["*"], dirs=["??z"])
#         ]
#         self.assertEqual(set(dir_list), {"baz"})
# 
#         with self.assertRaises(TypeError):
#             dir_list = [
#                 info.name
#                 for info in self.fs.filterdir("/", exclude_files=["*"], dirs="*.py")
#             ]
# 
    def test_getbytes(self):
        # Test getbytes method.
        all_bytes = b"".join(six.int2byte(n) for n in range(1, 256) if six.int2byte(n) not in [b'\r', b'\n'])
        all_bytes += b'\r\n'
        with self.fs.open(self.TEST_PATH + "1.eml", "wb") as f:
            f.write(all_bytes)
        self.assertEqual(self.fs.getbytes(self.TEST_PATH + "1.eml"), all_bytes)
        _all_bytes = self.fs.getbytes(self.TEST_PATH + "1.eml")
        self.assertIsInstance(_all_bytes, bytes)
        self.assertEqual(_all_bytes, all_bytes)
 
        with self.assertRaises(errors.ResourceNotFound):
            self.fs.getbytes(self.TEST_PATH + "1.eml/bar")
 
        self.fs.makedir(self.TEST_PATH + "baz")
        with self.assertRaises(errors.FileExpected):
            self.fs.getbytes(self.TEST_PATH + "baz")
# 
#     def test_getfile(self):
#         test_bytes = b"Hello, World"
#         self.fs.setbytes("hello.bin", test_bytes)
#         write_file = io.BytesIO()
#         self.fs.getfile("hello.bin", write_file)
#         self.assertEqual(write_file.getvalue(), test_bytes)
# 
#         with self.assertRaises(errors.ResourceNotFound):
#             self.fs.getfile("foo.bin", write_file)
# 
#     def test_isempty(self):
#         self.assertTrue(self.fs.isempty("/"))
#         self.fs.makedir("foo")
#         self.assertFalse(self.fs.isempty("/"))
#         self.assertTrue(self.fs.isempty("/foo"))
#         self.fs.create("foo/bar.txt")
#         self.assertFalse(self.fs.isempty("/foo"))
#         self.fs.remove("foo/bar.txt")
#         self.assertTrue(self.fs.isempty("/foo"))
# 
#     def test_setbytes(self):
#         all_bytes = b"".join(six.int2byte(n) for n in range(256))
#         self.fs.setbytes("foo", all_bytes)
#         with self.fs.open("foo", "rb") as f:
#             _bytes = f.read()
#         self.assertIsInstance(_bytes, bytes)
#         self.assertEqual(_bytes, all_bytes)
#         self.assert_bytes("foo", all_bytes)
#         with self.assertRaises(TypeError):
#             self.fs.setbytes("notbytes", "unicode")
# 

#     def test_gettext(self):
#         self.fs.makedir("foo")
#         with self.fs.open("foo/1.eml", "wt") as f:
#             f.write(UNICODE_TEXT)
#         text = self.fs.gettext("foo/1.eml")
#         self.assertIsInstance(text, text_type)
#         self.assertEqual(text, UNICODE_TEXT)
#         self.assert_text("foo/unicode.txt", UNICODE_TEXT)
#         
        
# 
#     def test_settext(self):
#         # Test settext method.
#         self.fs.settext("foo", "bar")
#         with self.fs.open("foo", "rt") as f:
#             foo = f.read()
#         self.assertEqual(foo, "bar")
#         self.assertIsInstance(foo, text_type)
#         with self.assertRaises(TypeError):
#             self.fs.settext("nottext", b"bytes")
# 
#     def test_setfile(self):
#         bytes_file = io.BytesIO(b"bar")
#         self.fs.setfile("foo", bytes_file)
#         with self.fs.open("foo", "rb") as f:
#             data = f.read()
#         self.assertEqual(data, b"bar")
# 
#     def test_setbinfile(self):
#         bytes_file = io.BytesIO(b"bar")
#         self.fs.setbinfile("foo", bytes_file)
#         with self.fs.open("foo", "rb") as f:
#             data = f.read()
#         self.assertEqual(data, b"bar")
# 
#     def test_bin_files(self):
#         # Check binary files.
#         with self.fs.openbin("foo1", "wb") as f:
#             text_type(f)
#             repr(f)
#             f.write(b"a")
#             f.write(b"b")
#             f.write(b"c")
#         self.assert_bytes("foo1", b"abc")
# 
#         # Test writelines
#         with self.fs.openbin("foo2", "wb") as f:
#             f.writelines([b"hello\n", b"world"])
#         self.assert_bytes("foo2", b"hello\nworld")
# 
#         # Test readline
#         with self.fs.openbin("foo2") as f:
#             self.assertEqual(f.readline(), b"hello\n")
#             self.assertEqual(f.readline(), b"world")
# 
#         # Test readlines
#         with self.fs.openbin("foo2") as f:
#             lines = f.readlines()
#         self.assertEqual(lines, [b"hello\n", b"world"])
#         with self.fs.openbin("foo2") as f:
#             lines = list(f)
#         self.assertEqual(lines, [b"hello\n", b"world"])
#         with self.fs.openbin("foo2") as f:
#             lines = []
#             for line in f:
#                 lines.append(line)
#         self.assertEqual(lines, [b"hello\n", b"world"])
#         with self.fs.openbin("foo2") as f:
#             print(repr(f))
#             self.assertEqual(next(f), b"hello\n")
# 
#         # Test truncate
#         with self.fs.open("foo2", "r+b") as f:
#             f.truncate(3)
#         self.assertEqual(self.fs.getsize("foo2"), 3)
#         self.assert_bytes("foo2", b"hel")
# 
#     def test_files(self):
#         # Test multiple writes
# 
#         with self.fs.open("foo1", "wt") as f:
#             text_type(f)
#             repr(f)
#             f.write("a")
#             f.write("b")
#             f.write("c")
#         self.assert_text("foo1", "abc")
# 
#         # Test writelines
#         with self.fs.open("foo2", "wt") as f:
#             f.writelines(["hello\n", "world"])
#         self.assert_text("foo2", "hello\nworld")
# 
#         # Test readline
#         with self.fs.open("foo2") as f:
#             self.assertEqual(f.readline(), "hello\n")
#             self.assertEqual(f.readline(), "world")
# 
#         # Test readlines
#         with self.fs.open("foo2") as f:
#             lines = f.readlines()
#         self.assertEqual(lines, ["hello\n", "world"])
#         with self.fs.open("foo2") as f:
#             lines = list(f)
#         self.assertEqual(lines, ["hello\n", "world"])
#         with self.fs.open("foo2") as f:
#             lines = []
#             for line in f:
#                 lines.append(line)
#         self.assertEqual(lines, ["hello\n", "world"])
# 
#         # Test truncate
#         with self.fs.open("foo2", "r+") as f:
#             f.truncate(3)
#         self.assertEqual(self.fs.getsize("foo2"), 3)
#         self.assert_text("foo2", "hel")
# 
#         with self.fs.open("foo2", "ab") as f:
#             f.write(b"p")
#         self.assert_bytes("foo2", b"help")
# 
#         # Test __del__ doesn't throw traceback
#         f = self.fs.open("foo2", "r")
#         del f
# 
#         with self.assertRaises(IOError):
#             with self.fs.open("foo2", "r") as f:
#                 f.write("no!")
# 
#         with self.assertRaises(IOError):
#             with self.fs.open("newfoo", "w") as f:
#                 f.read(2)
# 
#     def test_copy_file(self):
#         # Test fs.copy.copy_file
#         bytes_test = b"Hello, World"
#         self.fs.setbytes("foo.txt", bytes_test)
#         fs.copy.copy_file(self.fs, "foo.txt", self.fs, "bar.txt")
#         self.assert_bytes("bar.txt", bytes_test)
# 
#         mem_fs = open_fs("mem://")
# 
#         fs.copy.copy_file(self.fs, "foo.txt", mem_fs, "bar.txt")
#         self.assertEqual(mem_fs.getbytes("bar.txt"), bytes_test)
# 
#     def test_copy_structure(self):
#         mem_fs = open_fs("mem://")
#         self.fs.makedirs("foo/bar/baz")
#         self.fs.makedir("egg")
# 
#         fs.copy.copy_structure(self.fs, mem_fs)
#         expected = {"/egg", "/foo", "/foo/bar", "/foo/bar/baz"}
#         self.assertEqual(set(walk.walk_dirs(mem_fs)), expected)
# 
#     def _test_copy_dir(self, protocol):
#         # Test copy.copy_dir.
# 
#         # Test copying to a another fs
#         other_fs = open_fs(protocol)
#         self.fs.makedirs("foo/bar/baz")
#         self.fs.makedir("egg")
#         self.fs.settext("top.txt", "Hello, World")
#         self.fs.settext("/foo/bar/baz/test.txt", "Goodbye, World")
# 
#         fs.copy.copy_dir(self.fs, "/", other_fs, "/")
#         expected = {"/egg", "/foo", "/foo/bar", "/foo/bar/baz"}
#         self.assertEqual(set(walk.walk_dirs(other_fs)), expected)
#         self.assert_text("top.txt", "Hello, World")
#         self.assert_text("/foo/bar/baz/test.txt", "Goodbye, World")
# 
#         # Test copying a sub dir
#         other_fs = open_fs("mem://")
#         fs.copy.copy_dir(self.fs, "/foo", other_fs, "/")
#         self.assertEqual(list(walk.walk_files(other_fs)), ["/bar/baz/test.txt"])
# 
#         print("BEFORE")
#         self.fs.tree()
#         other_fs.tree()
#         fs.copy.copy_dir(self.fs, "/foo", other_fs, "/egg")
# 
#         print("FS")
#         self.fs.tree()
#         print("OTHER")
#         other_fs.tree()
#         self.assertEqual(
#             list(walk.walk_files(other_fs)),
#             ["/bar/baz/test.txt", "/egg/bar/baz/test.txt"],
#         )
# 
#     def _test_copy_dir_write(self, protocol):
#         # Test copying to this filesystem from another.
# 
#         other_fs = open_fs(protocol)
#         other_fs.makedirs("foo/bar/baz")
#         other_fs.makedir("egg")
#         other_fs.settext("top.txt", "Hello, World")
#         other_fs.settext("/foo/bar/baz/test.txt", "Goodbye, World")
#         fs.copy.copy_dir(other_fs, "/", self.fs, "/")
#         expected = {"/egg", "/foo", "/foo/bar", "/foo/bar/baz"}
#         self.assertEqual(set(walk.walk_dirs(self.fs)), expected)
#         self.assert_text("top.txt", "Hello, World")
#         self.assert_text("/foo/bar/baz/test.txt", "Goodbye, World")
# 
#     def test_copy_dir_mem(self):
#         # Test copy_dir with a mem fs.
#         self._test_copy_dir("mem://")
#         self._test_copy_dir_write("mem://")
# 
#     def test_copy_dir_temp(self):
#         # Test copy_dir with a temp fs.
#         self._test_copy_dir("temp://")
#         self._test_copy_dir_write("temp://")
# 
#     def _test_move_dir_write(self, protocol):
#         # Test moving to this filesystem from another.
#         other_fs = open_fs(protocol)
#         other_fs.makedirs("foo/bar/baz")
#         other_fs.makedir("egg")
#         other_fs.settext("top.txt", "Hello, World")
#         other_fs.settext("/foo/bar/baz/test.txt", "Goodbye, World")
# 
#         fs.move.move_dir(other_fs, "/", self.fs, "/")
# 
#         expected = {"/egg", "/foo", "/foo/bar", "/foo/bar/baz"}
#         self.assertEqual(other_fs.listdir("/"), [])
#         self.assertEqual(set(walk.walk_dirs(self.fs)), expected)
#         self.assert_text("top.txt", "Hello, World")
#         self.assert_text("/foo/bar/baz/test.txt", "Goodbye, World")
# 
#     def test_move_dir_mem(self):
#         self._test_move_dir_write("mem://")
# 
#     def test_move_dir_temp(self):
#         self._test_move_dir_write("temp://")
# 
#     def test_move_same_fs(self):
#         self.fs.makedirs("foo/bar/baz")
#         self.fs.makedir("egg")
#         self.fs.settext("top.txt", "Hello, World")
#         self.fs.settext("/foo/bar/baz/test.txt", "Goodbye, World")
# 
#         fs.move.move_dir(self.fs, "foo", self.fs, "foo2")
# 
#         expected = {"/egg", "/foo2", "/foo2/bar", "/foo2/bar/baz"}
#         self.assertEqual(set(walk.walk_dirs(self.fs)), expected)
#         self.assert_text("top.txt", "Hello, World")
#         self.assert_text("/foo2/bar/baz/test.txt", "Goodbye, World")
# 
#     def test_move_file_same_fs(self):
#         text = "Hello, World"
#         self.fs.makedir("foo").settext("test.txt", text)
#         self.assert_text("foo/test.txt", text)
# 
#         fs.move.move_file(self.fs, "foo/test.txt", self.fs, "foo/test2.txt")
#         self.assert_not_exists("foo/test.txt")
#         self.assert_text("foo/test2.txt", text)
# 
#     def _test_move_file(self, protocol):
#         other_fs = open_fs(protocol)
# 
#         text = "Hello, World"
#         self.fs.makedir("foo").settext("test.txt", text)
#         self.assert_text("foo/test.txt", text)
# 
#         with self.assertRaises(errors.ResourceNotFound):
#             fs.move.move_file(self.fs, "foo/test.txt", other_fs, "foo/test2.txt")
# 
#         other_fs.makedir("foo")
# 
#         fs.move.move_file(self.fs, "foo/test.txt", other_fs, "foo/test2.txt")
# 
#         self.assertEqual(other_fs.gettext("foo/test2.txt"), text)
# 
#     def test_move_file_mem(self):
#         self._test_move_file("mem://")
# 
#     def test_move_file_temp(self):
#         self._test_move_file("temp://")
# 
#     def test_copydir(self):
#         self.fs.makedirs("foo/bar/baz/egg")
#         self.fs.settext("foo/bar/foofoo.txt", "Hello")
#         self.fs.makedir("foo2")
#         self.fs.copydir("foo/bar", "foo2")
#         self.assert_text("foo2/foofoo.txt", "Hello")
#         self.assert_isdir("foo2/baz/egg")
#         self.assert_text("foo/bar/foofoo.txt", "Hello")
#         self.assert_isdir("foo/bar/baz/egg")
# 
#         with self.assertRaises(errors.ResourceNotFound):
#             self.fs.copydir("foo", "foofoo")
#         with self.assertRaises(errors.ResourceNotFound):
#             self.fs.copydir("spam", "egg", create=True)
#         with self.assertRaises(errors.DirectoryExpected):
#             self.fs.copydir("foo2/foofoo.txt", "foofoo.txt", create=True)
# 
#     def test_movedir(self):
#         self.fs.makedirs("foo/bar/baz/egg")
#         self.fs.settext("foo/bar/foofoo.txt", "Hello")
#         self.fs.makedir("foo2")
#         self.fs.movedir("foo/bar", "foo2")
#         self.assert_text("foo2/foofoo.txt", "Hello")
#         self.assert_isdir("foo2/baz/egg")
#         self.assert_not_exists("foo/bar/foofoo.txt")
#         self.assert_not_exists("foo/bar/baz/egg")
# 
#         # Check moving to an unexisting directory
#         with self.assertRaises(errors.ResourceNotFound):
#             self.fs.movedir("foo", "foofoo")
# 
#         # Check moving an unexisting directory
#         with self.assertRaises(errors.ResourceNotFound):
#             self.fs.movedir("spam", "egg", create=True)
# 
#         # Check moving a file
#         with self.assertRaises(errors.DirectoryExpected):
#             self.fs.movedir("foo2/foofoo.txt", "foo2/baz/egg")
# 
#     def test_match(self):
#         self.assertTrue(self.fs.match(["*.py"], "foo.py"))
#         self.assertEqual(
#             self.fs.match(["*.py"], "FOO.PY"),
#             self.fs.getmeta().get("case_insensitive", False),
#         )
# 
#     def test_tree(self):
#         self.fs.makedirs("foo/bar")
#         self.fs.create("test.txt")
#         write_tree = io.StringIO()
#         self.fs.tree(file=write_tree)
#         written = write_tree.getvalue()
#         expected = "|-- foo\n|   `-- bar\n`-- test.txt\n"
#         self.assertEqual(expected, written)
# 
#     def test_unicode_path(self):
#         if not self.fs.getmeta().get("unicode_paths", False):
#             self.skipTest("the filesystem does not support unicode paths.")
# 
#         self.fs.makedir("földér")
#         self.fs.settext("☭.txt", "Smells like communism.")
#         self.fs.setbytes("földér/☣.txt", b"Smells like an old syringe.")
# 
#         self.assert_isdir("földér")
#         self.assertEqual(["☣.txt"], self.fs.listdir("földér"))
#         self.assertEqual("☣.txt", self.fs.getinfo("földér/☣.txt").name)
#         self.assert_text("☭.txt", "Smells like communism.")
#         self.assert_bytes("földér/☣.txt", b"Smells like an old syringe.")
# 
#         if self.fs.hassyspath("földér/☣.txt"):
#             self.assertTrue(os.path.exists(self.fs.getsyspath("földér/☣.txt")))
# 
#         self.fs.remove("földér/☣.txt")
#         self.assert_not_exists("földér/☣.txt")
#         self.fs.removedir("földér")
#         self.assert_not_exists("földér")
# 
#     def test_case_sensitive(self):
#         meta = self.fs.getmeta()
#         if "case_insensitive" not in meta:
#             self.skipTest("case sensitivity not known")
# 
#         if meta.get("case_insensitive", False):
#             self.skipTest("the filesystem is not case sensitive.")
# 
#         self.fs.makedir("foo")
#         self.fs.makedir("Foo")
#         self.fs.touch("fOO")
# 
#         self.assert_exists("foo")
#         self.assert_exists("Foo")
#         self.assert_exists("fOO")
#         self.assert_not_exists("FoO")
# 
#         self.assert_isdir("foo")
#         self.assert_isdir("Foo")
#         self.assert_isfile("fOO")
# 
#     def test_glob(self):
#         self.assertIsInstance(
#             self.fs.glob,
#             glob.BoundGlobber
#         )
