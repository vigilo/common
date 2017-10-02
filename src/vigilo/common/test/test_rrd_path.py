# -*- coding: utf-8 -*-
# Copyright (C) 2006-2016 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""Teste la génération du chemin vers les fichiers RRD."""
import unittest
from vigilo.common import get_rrd_path

class TestRRDPath(unittest.TestCase):
    def test_default_values(self):
        """Valeurs par défaut des paramètres pour 'get_rrd_path'."""
        self.assertEqual(
            get_rrd_path("localhost"),
            "/var/lib/vigilo/rrds/localhost"
        )

    def test_non_default_base_dir(self):
        """Surcharge du dossier par défaut des RRDs."""
        self.assertEqual(
            get_rrd_path("localhost", base_dir="/tmp"),
            "/tmp/localhost"
        )

    def test_path_modes(self):
        """Différents modes de hachage pour le chemin."""
        self.assertEqual(
            get_rrd_path("localhost", path_mode="flat"),
            "/var/lib/vigilo/rrds/localhost"
        )
        self.assertEqual(
            get_rrd_path("localhost", path_mode="name"),
            "/var/lib/vigilo/rrds/l/lo/localhost"
        )
        self.assertEqual(
            get_rrd_path("localhost", path_mode="hash"),
            "/var/lib/vigilo/rrds/4/42/localhost"
        )

    def test_path_with_ds(self):
        """Chemin complet vers le fichier RRD."""
        self.assertEqual(
            get_rrd_path("localhost", ds="Ping", path_mode="flat"),
            "/var/lib/vigilo/rrds/localhost/Ping.rrd"
        )
        self.assertEqual(
            get_rrd_path("localhost", ds="Ping", path_mode="name"),
            "/var/lib/vigilo/rrds/l/lo/localhost/Ping.rrd"
        )
        self.assertEqual(
            get_rrd_path("localhost", ds="Ping", path_mode="hash"),
            "/var/lib/vigilo/rrds/4/42/localhost/Ping.rrd"
        )

    def test_unicode(self):
        """Chemin complet vers le fichier RRD avec paramètres en unicode."""
        self.assertEqual(
            get_rrd_path(u"testserver éçà", u"Ping' éçà", path_mode="flat"),
            "/var/lib/vigilo/rrds/testserver+%C3%A9%C3%A7%C3%A0/"
            "Ping%27+%C3%A9%C3%A7%C3%A0.rrd"
        )
        self.assertEqual(
            get_rrd_path(u"testserver éçà", u"Ping' éçà", path_mode="name"),
            "/var/lib/vigilo/rrds/t/te/testserver+%C3%A9%C3%A7%C3%A0/"
            "Ping%27+%C3%A9%C3%A7%C3%A0.rrd"
        )
        self.assertEqual(
            get_rrd_path(u"testserver éçà", u"Ping' éçà", path_mode="hash"),
            "/var/lib/vigilo/rrds/0/08/testserver+%C3%A9%C3%A7%C3%A0/"
            "Ping%27+%C3%A9%C3%A7%C3%A0.rrd"
        )
