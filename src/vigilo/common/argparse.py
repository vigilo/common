# -*- coding: utf-8 -*-
# Copyright (C) 2006-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>
"""
Intégration de argparse dans Vigilo.
"""
from __future__ import absolute_import
import gettext

def prepare_argparse():
    """
    Prépare les traductions pour les messages de la bibliothèque argparse.
    """
    # argparse utilise le domaine par défaut pour les traductions.
    # On définit explicitement le domaine par défaut ici. Ceci permet de
    # définir les traductions pour les textes de argparse dans vigilo-common.
    gettext.textdomain('vigilo-common')

    def _(s):
        """
        Fonction de traduction fictive.

        Le but ici est simplement de faire en sorte que les scripts
        d'extraction des textes à traduire "voient" les messages
        associés à argparse.
        """
        return s

    # Permet de traduire les textes internes à argparse
    # comme s'ils faisaient partie de vigilo-common.
    _('usage: ')
    _('conflicting option string(s): %s')
    _('subcommands')
    _('unrecognized arguments: %s')
    _('expected one argument')
    _('expected at most one argument')
    _('expected at least one argument')
    _('expected %s argument(s)')
    _('invalid choice: %r (choose from %s)')
    _('positional arguments')
    _('optional arguments')
    _('too few arguments')
    _('argument %s is required')
    _('one of the arguments %s is required')
    _('%s: error: %s\n')
    _('show this help message and exit')
    _("show program's version number and exit")
