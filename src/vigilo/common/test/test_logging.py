# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2019 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>
"""
Tests portant sur la gestion des journaux.
"""

from __future__ import absolute_import

import os
import sys
import tempfile
import unittest
import shutil
import logging

from vigilo.common.conf import settings
from vigilo.common.logging import fileConfig, get_logger

class Logging(unittest.TestCase):
    """Tests portant sur la configuration des journaux."""

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

    def test_handlers_args(self):
        """Lecture des arguments d'un 'handler'."""
        # Note : on ne peut pas changer la configuration du logger_root
        # car nose effectue déjà des modifications de celui-ci (qui sont
        # prioritaires sur notre configuration).
        self.load_conf_from_string("""
[loggers]
keys=test

[handlers]
keys=test

[logger_test]
level=DEBUG
handlers=test
qualname=%s

[handler_test]
class=StreamHandler
level=INFO
; En remplace le flux par défaut (stderr) par stdout.
args=(sys.stdout, )
""" % __name__)
        fileConfig()
        logger = get_logger(__name__)

        # Le logger doit avoir le bon niveau, le bon nombre d'handlers
        # et surtout le handler doit avoir la bonne configuration de flux.
        self.assertEqual(logger.level, logging.DEBUG)
        self.assertEqual(len(logger.handlers), 1)
        handler = logger.handlers[0]
        self.assertTrue(isinstance(handler, logging.StreamHandler),
                        handler.__class__.__name__)
        self.assertEqual(handler.level, logging.INFO)
        self.assertEqual(handler.stream, sys.stdout)
