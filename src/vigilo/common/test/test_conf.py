# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>
"""Tests portant sur la gestion de la configuration."""

from __future__ import absolute_import, print_function

import runpy
import os
import sys
import tempfile
import unittest
import shutil
# Import from io if we target 2.6
from cStringIO import StringIO

from vigilo.common.conf import settings
from vigilo.common.logging import fileConfig


class Conf(unittest.TestCase):
    """Tests sur la gestion de la configuration."""

    def setUp(self):
        """Préparatifs avant chaque test."""
        settings.reset()
        self.tmpdir = tempfile.mkdtemp(prefix="vigilo-common-tests-")

    def tearDown(self):
        """Nettoyage après chaque test."""
        shutil.rmtree(self.tmpdir)
        try:
            del os.environ["VIGILO_SETTINGS"]
        except KeyError:
            pass


    def load_conf_from_string(self, data):
        """
        Chargement d'une configuration à partir
        d'une chaîne de caractères.
        """
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
        conf1.write("[include]\ninclude = %s" % conffile2)
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
        conf1.write("[include]\ninclude = %s" % conffile2)
        conf1.close()
        conf2 = open(conffile2, "w")
        conf2.write("[include]\ninclude = %s" % conffile3)
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
        conf1.write("[include]\ninclude = %s\n[section]\nkey=value1"
                    % conffile2)
        conf1.close()
        conf2 = open(conffile2, "w")
        conf2.write("[section]\nkey=value2\n")
        conf2.close()
        settings.load_file(conffile1)
        self.assertTrue("section" in settings)
        self.assertEqual(settings["section"].get("key"), "value1")


    def test_include_list(self):
        """Directive "include" : utilisation d'une liste."""
        conffile1 = os.path.join(self.tmpdir, "test-1.ini")
        conffile2 = os.path.join(self.tmpdir, "test-2.ini")
        conffile3 = os.path.join(self.tmpdir, "test-3.ini")
        conf1 = open(conffile1, "w")
        conf1.write("[include]\ninclude = %s, %s" % (conffile2, conffile3))
        conf1.close()
        conf2 = open(conffile2, "w")
        conf2.write("[section]\nkey=value\n")
        conf2.close()
        conf3 = open(conffile3, "w")
        conf3.write("[section]\nkey2=value2\n")
        conf3.close()
        settings.load_file(conffile1)
        self.assertTrue("section" in settings)
        self.assertEqual(settings["section"].get("key"), "value")
        self.assertTrue(conffile2 in settings.filenames)
        self.assertEqual(settings["section"].get("key2"), "value2")
        self.assertTrue(conffile3 in settings.filenames)


    def test_include_empty_list(self):
        """Directive "include" : utilisation d'une liste vide."""
        conffile1 = os.path.join(self.tmpdir, "test-1.ini")
        conf1 = open(conffile1, "w")
        conf1.write("[include]\ninclude = ")
        conf1.close()
        settings.load_file(conffile1)


    def test_include_nonexistant_file(self):
        """Directive "include" : fichier non existant."""
        conffile1 = os.path.join(self.tmpdir, "test-1.ini")
        conf1 = open(conffile1, "w")
        conf1.write("[include]\ninclude = /nonexistant")
        conf1.close()
        settings.load_file(conffile1)


    def test_include_directory(self):
        """Directive "include" : chargement d'un dossier."""
        conffile0 = os.path.join(self.tmpdir, "test.ini")
        os.mkdir(os.path.join(self.tmpdir, "conf.d"))
        conffile1 = os.path.join(self.tmpdir, "conf.d", "test-1.ini")
        conffile2 = os.path.join(self.tmpdir, "conf.d", "test-2.ini")
        conf0 = open(conffile0, "w")
        conf0.write("[include]\ninclude = %s"
                    % os.path.join(self.tmpdir, "conf.d"))
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
        self.assertTrue(conffile1 in settings.filenames)
        self.assertEqual(settings["section"].get("key2"), "value2")
        self.assertTrue(conffile2 in settings.filenames)


    def test_include_directory_overload(self):
        """Directive "include" : surcharge lors du chargement d'un dossier."""
        conffile0 = os.path.join(self.tmpdir, "test.ini")
        os.mkdir(os.path.join(self.tmpdir, "conf.d"))
        conffile1 = os.path.join(self.tmpdir, "conf.d", "test-1.ini")
        conffile2 = os.path.join(self.tmpdir, "conf.d", "test-2.ini")
        conf0 = open(conffile0, "w")
        conf0.write("[include]\ninclude = %s"
                    % os.path.join(self.tmpdir, "conf.d"))
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
        conffile1 = os.path.join(self.tmpdir, "test-1.ini")
        conffile2 = os.path.join(self.tmpdir, "test-2.ini")
        conf1 = open(conffile1, "w")
        conf1.write("[include]\ninclude = %s" % conffile2)
        conf1.close()
        conf2 = open(conffile2, "w")
        conf2.write("[include]\ninclude = %s" % conffile1)
        conf2.close()
        settings.load_file(conffile1)
        print(settings.filenames)
        self.assertEqual(len(settings.filenames), 2)


    def test_reload_and_load_twice(self):
        """Chargement de la conf deux fois V.S. utilisation de reload()"""
        conffile = os.path.join(self.tmpdir, "test.ini")
        conf = open(conffile, "w")
        conf.write("[section]\nkey=value\n")
        conf.close()
        settings.load_file(conffile)
        settings["section"]["key"] = "othervalue"
        settings.load_file(conffile) # ne change rien, fichier déjà chargé
        self.assertEqual(settings["section"]["key"], "othervalue")
        settings.reload() # Retour à la valeur d'origine
        self.assertEqual(settings["section"]["key"], "value")

    def test_multiline_options(self):
        """Valeur d'une option qui occupe plusieurs lignes."""
        self.load_conf_from_string("""
[section]
key='''Cette valeur
se trouve
sur plusieurs lignes'''
""")
        self.assertEqual(settings["section"].get("key"), """Cette valeur
se trouve
sur plusieurs lignes""")
        # Le chargement d'un fichier contenant des valeurs multi-lignes
        # ne doit pas perturber le fonctionnement du module de logs.
        fileConfig()

    def test_args_in_non_logging_config(self):
        """
        Option 'args' en dehors de la configuration des journaux.

        Lorsqu'elle utilisée en dehors de la configuration d'un handler
        lors de la configuration des journaux, la détection automatique
        des listes doit être appliquée à l'option "args".
        """
        self.load_conf_from_string("""
[section]
; La clé ressemble à une configuration de handler dans les logs,
; mais ce n'en est pas une. Donc ici on doit obtenir une liste
; contenant 2 valeurs : "(sys.stdout" et ")".
args=(sys.stdout, )
""")
        expected = ['(sys.stdout', ')']
        self.assertEqual(settings["section"].get("args"), expected)
