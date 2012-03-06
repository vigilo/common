# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import absolute_import

import runpy
import os
import sys
import tempfile
import unittest
import shutil
# Import from io if we target 2.6
from cStringIO import StringIO

from vigilo.common.conf import settings, ConfigParseError


class Conf(unittest.TestCase):

    def setUp(self):
        settings.reset()
        self.tmpdir = tempfile.mkdtemp(prefix="vigilo-common-tests-")

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        try:
            del os.environ["VIGILO_SETTINGS"]
        except KeyError:
            pass


    def load_conf_from_string(self, data):
        conffile = os.path.join(self.tmpdir, "test.ini")
        conf = open(conffile, "w")
        conf.write(data)
        conf.close()
        settings.load_file(conffile)
        os.environ["VIGILO_SETTINGS"] = conffile


    def test_loading_with_semicolons_as_comments(self):
        """Point-virgule comme début de commentaire."""
        self.load_conf_from_string("""
[section]
; pre-member comment
key=value ; inline comment
; yet again!
""")
        self.assertEqual(settings["section"].get("key"), "value")
        self.assertEqual(settings["section"].comments["key"],
                         ["; pre-member comment"])
        self.assertEqual(settings["section"].inline_comments["key"],
                         "; inline comment")


    def test_cmdline(self):
        """Utilisation du script CLI vigilo-config."""
        # Normally called from the command line, this is just for test coverage
        # See the memcached runit service for command-line use.
        self.load_conf_from_string(
                    """[test-section]\nTEST_KEY = test_value\n""")
        oldout, sys.stdout = sys.stdout, StringIO()
        try:
            # pylint: disable-msg=E1103
            sys.argv[1:] = ['--get', 'TEST_KEY', "--section", "test-section"]
            try:
                runpy.run_module('vigilo.common.conf',
                        run_name='__main__', alter_sys=True)
            except SystemExit:
                pass
            self.assertEqual(sys.stdout.getvalue().strip(),
                             "test_value")
            sys.stdout.seek(0)
            sys.stdout.truncate()

            sys.argv[1:] = []
            try:
                runpy.run_module('vigilo.common.conf',
                        run_name='__main__', alter_sys=True)
            except SystemExit:
                pass
            self.assertEqual(sys.stdout.getvalue(), '')
            sys.stdout.seek(0)
            sys.stdout.truncate()

        finally:
            sys.stdout = oldout


    def test_include(self):
        """Directive "include" : cas simple."""
        conffile1 = os.path.join(self.tmpdir, "test-1.ini")
        conffile2 = os.path.join(self.tmpdir, "test-2.ini")
        conf1 = open(conffile1, "w")
        conf1.write("include = %s" % conffile2)
        conf1.close()
        conf2 = open(conffile2, "w")
        conf2.write("[section]\nkey=value\n")
        conf2.close()
        settings.load_file(conffile1)
        self.assertTrue("section" in settings)
        self.assertEqual(settings["section"].get("key"), "value")


    def test_include_2_levels(self):
        """Directive "include" : sur deux niveaux."""
        conffile1 = os.path.join(self.tmpdir, "test-1.ini")
        conffile2 = os.path.join(self.tmpdir, "test-2.ini")
        conffile3 = os.path.join(self.tmpdir, "test-3.ini")
        conf1 = open(conffile1, "w")
        conf1.write("include = %s" % conffile2)
        conf1.close()
        conf2 = open(conffile2, "w")
        conf2.write("include = %s" % conffile3)
        conf2.close()
        conf3 = open(conffile3, "w")
        conf3.write("[section]\nkey=value\n")
        conf3.close()
        settings.load_file(conffile1)
        self.assertTrue("section" in settings)
        self.assertEqual(settings["section"].get("key"), "value")


    def test_include_overload(self):
        """Directive "include" : surcharge des valeurs."""
        conffile1 = os.path.join(self.tmpdir, "test-1.ini")
        conffile2 = os.path.join(self.tmpdir, "test-2.ini")
        conf1 = open(conffile1, "w")
        conf1.write("include = %s\n[section]\nkey=value1" % conffile2)
        conf1.close()
        conf2 = open(conffile2, "w")
        conf2.write("[section]\nkey=value2\n")
        conf2.close()
        settings.load_file(conffile1)
        self.assertTrue("section" in settings)
        self.assertEqual(settings["section"].get("key"), "value1")

    def test_include_directory(self):
        """Directive "include" : chargement d'un dossier."""
        conffile0 = os.path.join(self.tmpdir, "test.ini")
        os.mkdir(os.path.join(self.tmpdir, "conf.d"))
        conffile1 = os.path.join(self.tmpdir, "conf.d", "test-1.ini")
        conffile2 = os.path.join(self.tmpdir, "conf.d", "test-2.ini")
        conf0 = open(conffile0, "w")
        conf0.write("include = %s" % os.path.join(self.tmpdir, "conf.d"))
        conf0.close()
        conf1 = open(conffile1, "w")
        conf1.write("[section]\nkey1=value1\n")
        conf1.close()
        conf2 = open(conffile2, "w")
        conf2.write("[section]\nkey2=value2\n")
        conf2.close()
        settings.load_file(conffile0)
        self.assertTrue("section" in settings)
        self.assertEqual(settings["section"].get("key1"), "value1")
        self.assertEqual(settings["section"].get("key2"), "value2")

    def test_include_directory_overload(self):
        """Directive "include" : surcharge lors du chargement d'un dossier."""
        conffile0 = os.path.join(self.tmpdir, "test.ini")
        os.mkdir(os.path.join(self.tmpdir, "conf.d"))
        conffile1 = os.path.join(self.tmpdir, "conf.d", "test-1.ini")
        conffile2 = os.path.join(self.tmpdir, "conf.d", "test-2.ini")
        conf0 = open(conffile0, "w")
        conf0.write("include = %s" % os.path.join(self.tmpdir, "conf.d"))
        conf0.close()
        conf1 = open(conffile1, "w")
        conf1.write("[section]\nkey=value1\n")
        conf1.close()
        conf2 = open(conffile2, "w")
        conf2.write("[section]\nkey=value2\n")
        conf2.close()
        settings.load_file(conffile0)
        self.assertTrue("section" in settings)
        # La valeur correspond à celle indiquée
        # dans le dernier fichier chargé.
        self.assertEqual(settings["section"].get("key"), "value2")

    def test_include_loop(self):
        """Directive "include" : boucle."""
        # @FIXME: Ne fonctionne pas correctement : la plupart des modules
        # essayent de charger plusieurs fois les fichiers de configuration,
        # en particulier au niveau des tests unitaires.
        return
        conffile1 = os.path.join(self.tmpdir, "test-1.ini")
        conffile2 = os.path.join(self.tmpdir, "test-2.ini")
        conf1 = open(conffile1, "w")
        conf1.write("include = %s" % conffile2)
        conf1.close()
        conf2 = open(conffile2, "w")
        conf2.write("include = %s" % conffile1)
        conf2.close()
        self.assertRaises(ConfigParseError, settings.load_file, conffile1)
