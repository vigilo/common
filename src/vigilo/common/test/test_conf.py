# vim: set fileencoding=utf-8 sw=4 ts=4 et :
from __future__ import absolute_import

import runpy
import os
import sys
import tempfile
import unittest
# Import from io if we target 2.6
from cStringIO import StringIO

from vigilo.common.conf import settings

from nose.tools import assert_raises


class Conf(unittest.TestCase):

    def setUp(self):
        settings.reset()
        self.tmpfile_fd, self.tmpfile = tempfile.mkstemp(dir="/dev/shm")

    def tearDown(self):
        os.remove(self.tmpfile)

    def load_conf_from_string(self, data):
        conffile = os.fdopen(self.tmpfile_fd, "w")
        conffile.write(data)
        conffile.close()
        settings.load_file(self.tmpfile)
        os.environ["VIGILO_SETTINGS"] = self.tmpfile

    def test_loading_with_semicolons_as_comments(self):
        self.load_conf_from_string("""
[section]
; pre-member comment
key=value ; inline comment
; yet again!
""")
        self.assertEqual(settings["section"].get("key"), "value")
        self.assertEqual(settings["section"].comments["key"], ["; pre-member comment"])
        self.assertEqual(settings["section"].inline_comments["key"], "; inline comment")

    def test_cmdline(self):
        # Normally called from the command line, this is just for test coverage
        # See the memcached runit service for command-line use.
        self.load_conf_from_string("""[test-section]\nTEST_KEY = test_value\n""")
        oldout, sys.stdout = sys.stdout, StringIO()
        try:
            sys.argv[1:] = ['--get', 'TEST_KEY', "--section", "test-section"]
            try:
                runpy.run_module('vigilo.common.conf',
                        run_name='__main__', alter_sys=True)
            except SystemExit, e:
                pass
            assert sys.stdout.getvalue().strip() == "test_value" # pylint: disable-msg=E1103
            sys.stdout.seek(0)
            sys.stdout.truncate()

            sys.argv[1:] = []
            try:
                runpy.run_module('vigilo.common.conf',
                        run_name='__main__', alter_sys=True)
            except SystemExit, e:
                pass
            assert sys.stdout.getvalue() == '' # pylint: disable-msg=E1103
            sys.stdout.seek(0)
            sys.stdout.truncate()

        finally:
            sys.stdout = oldout

