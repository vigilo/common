# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

import unittest
from vigilo.common.logging import get_error_message

class TestExceptionMessage(unittest.TestCase):
    """
    Teste la récupération du message d'erreur d'une exception.
    """

    def test_unicode_exception(self):
        """Message d'erreur d'une exception Unicode."""
        e = ValueError(u'Some error éçà')
        self.assertEquals(u'Some error éçà', get_error_message(e))

    def test_utf8_str_exception(self):
        """Message d'erreur d'une exception UTF-8."""
        # "éçà" encodé en UTF-8.
        e = ValueError('Some error \xC3\xA9\xC3\xA7\xC3\xA0')
        self.assertEquals(u'Some error éçà', get_error_message(e))

    def test_unknown_str_exception(self):
        """Message d'erreur d'une exception avec encodage inconnu."""
        # "éçà" encodé en ISO-8859-15.
        e = ValueError('Some error \xE9\xE7\xE0')
        msg = get_error_message(e)
        self.assertTrue(isinstance(msg, unicode))
