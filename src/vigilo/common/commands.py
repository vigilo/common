# -*- coding: utf-8 -*-
# Copyright (C) 2006-2016 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Outils pour la manipulation de fichiers de traductions (catalogs).
"""
import os.path, os
from distutils import log
from distutils.cmd import Command
from distutils.errors import DistutilsOptionError

from babel import Locale
from babel.core import UnknownLocaleError
from babel.messages.pofile import read_po, write_po

class identity_catalog(Command):
    """
    Génère un catalogue tel que les traductions sont équivalentes
    aux messages à traduire (similaire à la commande msgen sous Linux).
    """
    # pylint: disable-msg=W0201,C0103,W0232
    # fonctionnement normal d'un plugin distutils

    description = 'generates an identity catalog, like msgen'
    user_options = [
        ('domain=', 'D',
         "domain of PO file (default 'messages')"),
        ('input-file=', 'i',
         'name of the input file'),
        ('output-dir=', 'd',
         'path to output directory'),
        ('output-file=', 'o',
         "name of the output file (default "
         "'<output_dir>/<locale>/LC_MESSAGES/<domain>.po')"),
        ('locale=', 'l',
         'locale of the catalog to "translate"'),
#        ('no-location', None,
#         'do not include location comments with filename and line number'),
#        ('output-file=', 'o',
#         'name of the output file'),
#        ('width=', 'w',
#         'set output line width (default 76)'),
#        ('no-wrap', None,
#         'do not break long message lines, longer than the output line width, '
#         'into several lines'),
#        ('sort-output', None,
#         'generate sorted output (default False)'),
#        ('sort-by-file', None,
#         'sort output by file location (default False)'),
    ]
    boolean_options = [
#        'no-location',
#        'no-wrap',
#        'sort-output',
#        'sort-by-file',
    ]

    def initialize_options(self):
        self.output_dir = None
        self.output_file = None
        self.input_file = None
        self.locale = None
        self.domain = 'messages'

    def finalize_options(self):
        if not self.input_file:
            raise DistutilsOptionError('you must specify the input file')

        if not self.locale:
            raise DistutilsOptionError('you must provide a locale for the '
                                       'catalog')

        if not self.output_file and not self.output_dir:
            raise DistutilsOptionError('you must specify the output directory')
        if not self.output_file:
            self.output_file = os.path.join(self.output_dir, self.locale,
                                            'LC_MESSAGES', self.domain + '.po')

        try:
            self._locale = Locale.parse(self.locale)
        except UnknownLocaleError, e:
            raise DistutilsOptionError(e)

        if not os.path.exists(os.path.dirname(self.output_file)):
            os.makedirs(os.path.dirname(self.output_file))

    def run(self):
        log.info('translating catalog %r based on %r', self.output_file,
                 self.input_file)

        infile = open(self.input_file, 'r')
        try:
            # Although reading from the catalog template, read_po must be fed
            # the locale in order to correcly calculate plurals
            catalog = read_po(infile, locale=self.locale)
        finally:
            infile.close()

        catalog.locale = self._locale
        catalog.fuzzy = False

        for message in catalog:
            if message.id:
                # Recopie de l'id du message dans la traduction.
                message.string = message.id
                catalog[message.id] = message

        outfile = open(self.output_file, 'w')
        try:
            write_po(outfile, catalog)
        finally:
            outfile.close()

