# -*- coding: utf-8 -*-
# Copyright (C) 2006-2021 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Commandes supplémentaires pour setuptools.
"""
import io
import os
import re

from babel import Locale
from babel.core import UnknownLocaleError
from babel.messages.pofile import read_po, write_po
from babel.messages.frontend import compile_catalog

from distutils import log
from distutils.cmd import Command
from distutils.command.build import build as orig_build
from distutils.command.install_data import install_data as orig_install_data
from distutils.errors import DistutilsOptionError, DistutilsSetupError

from setuptools.command.install import install as orig_install

try:
    import simplejson as json
except ImportError:
    import json


def validate_build_vars(dist, attr, value):
    """
    Valide la valeur de l'attribut "vigilo_build_vars" de setup(),
    ajoute dynamiquement les variables à la commande "install"
    et prépare les classes qui implémentent les commandes setuptools.
    """
    if not isinstance(value, dict):
        raise DistutilsSetupError(
            "%r must be a dictionary of dictionaries (got %r)" % (attr, type(value))
        )
    pattern = re.compile('^[a-zA-Z][a-zA-Z0-9-]*$')
    opts = []
    for k, vconf in value.items():
        if not pattern.match(k):
            raise DistutilsSetupError('Invalid variable name "%s"' % k)

        if not isinstance(vconf, dict) or \
            not isinstance(vconf.get('default'), str) or \
            not isinstance(vconf.get('description'), str):
            raise DistutilsSetupError(
                "Each variable must be a dictionary defining the 'default' "
                "value and the 'description' string"
            )
        opts.append( ('with-%s=' % k, None, "%s (%s)" %
                      (vconf['description'], vconf['default'])) )

    # Patch the commands' classes automatically.
    install.user_options = orig_install.user_options + opts
    classes = {
        "compile_catalog": compile_catalog,
        "build": build,
        "install": install,
        "install_data": install_data,
    }
    for cmd, cls in classes.items():
        dist.cmdclass.setdefault(cmd, cls)


class build(orig_build):
    """
    Extension de la commande "build" de distutils qui appelle automatiquement
    "compile_catalog" lorsque le composant dispose de traductions.
    """
    def has_i18n(self):
        return getattr(self.distribution, 'message_extractors', None)

    sub_commands = [
        ('compile_catalog', has_i18n),
    ] + orig_build.sub_commands


class install(orig_install):
    def initialize_options(self):
        orig_install.initialize_options(self)
        variables = getattr(self.distribution, 'vigilo_build_vars', {}).items()
        for k, vconf in variables:
            setattr(self, 'with_%s' % k.replace('-', '_'), vconf['default'])

    def finalize_options(self):
        orig_install.finalize_options(self)
        variables = {}
        for k in getattr(self.distribution, 'vigilo_build_vars', {}):
            variables[k] = getattr(self, 'with_%s' % k.replace('-', '_'))
        self.variables = variables


class install_data(orig_install_data):
    """
    Extension de la commande "install_data" de setuptools pour remplacer
    automatiquement les variables de construction par leur valeur.

    La substitution est faite à la fois dans le chemin de destination
    du fichier et dans son contenu, dès lors que le nom du fichier source
    se termine par ".in". Le suffixe est retiré du nom du fichier final.
    """
    def finalize_options(self):
        orig_install_data.finalize_options(self)
        cmd = self.get_finalized_command("install")
        self.install_cmd = cmd

        if not cmd.variables:
            self.subst_pattern = None
        else:
            pattern = '(%s)' % '|'.join("@%s@" % k for k in cmd.variables)
            self.subst_pattern = re.compile(pattern)
            self.data_files = [ (self.substitute(f[0]), f[1])
                                for f in self.data_files]

    def _subst_replace(self, match):
        return self.install_cmd.variables[match.group(1)[1:-1]]

    def substitute(self, value):
        if not self.subst_pattern:
            return value
        return self.subst_pattern.sub(self._subst_replace, value)

    def substitute_file(self, outf, inf):
        log.info("creating '%s' based on '%s'" % (outf, os.path.basename(inf)))
        if self.dry_run:
            return

        with io.open(outf, 'w', encoding='utf-8') as outfd:
            with io.open(inf, 'r', encoding='utf-8') as infd:
                os.unlink(inf)
                outfd.write(self.substitute(infd.read()))

    def copy_file(self, srcfile, target, *args, **kwargs):
        target = self.substitute(target)
        outf, copied = orig_install_data.copy_file(self, srcfile, target,
                                                   *args, **kwargs)
        if copied and outf.endswith('.in'):
            self.substitute_file(outf[:-3], outf)
            outf = outf[:-3]
        return outf, copied


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
        except UnknownLocaleError as e:
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


class compile_catalog_plusjs(compile_catalog):
    """
    An extended command that writes all message strings that occur in
    JavaScript files to a JavaScript file along with the .mo file.

    Unfortunately, babel's setup command isn't very extensible,
    so most of the run() method's code is duplicated here.
    """

    def run(self):
        compile_catalog.run(self)

        po_files = []
        js_files = []

        if isinstance(self.domain, list):
            domains = self.domain
        else:
            domains = [self.domain]

        if not self.input_file:
            if self.locale:
                for domain in domains:
                    basename = os.path.join(self.directory, self.locale,
                                            'LC_MESSAGES', domain)
                    po_files.append( (self.locale, basename + '.po') )
                    js_files.append( basename + '.js')
            else:
                for locale in os.listdir(self.directory):
                    for domain in domains:
                        basename = os.path.join(self.directory, locale,
                                                'LC_MESSAGES', domain)
                        if os.path.exists(basename + '.po'):
                            po_files.append( (locale, basename + '.po') )
                            js_files.append(basename + '.js')
        else:
            po_files.append( (self.locale, self.input_file) )
            if self.output_file:
                js_files.append(self.output_file)
            else:
                for domain in domains:
                    js_files.append(os.path.join(
                        self.directory,
                        self.locale,
                        'LC_MESSAGES',
                        domain + '.js'
                     ))

        for js_file, (locale, po_file) in zip(js_files, po_files):
            infile = open(po_file, 'r')
            try:
                catalog = read_po(infile, locale)
            finally:
                infile.close()

            if catalog.fuzzy and not self.use_fuzzy:
                continue

            log.info('writing JavaScript strings in catalog %r to %r',
                     po_file, js_file)

            jscatalog = {}
            for message in catalog:
                # Si le message n'a pas encore été traduit,
                # on ne l'ajoute pas. Le message d'origine
                # (non traduit) sera renvoyé.
                if not message.string:
                    continue

                # On n'ajoute le message au fichier de traduction JS
                # auto-généré que si le message est utilisé dans du
                # code JavaScript.
                if any(x[0].endswith('.js') for x in message.locations):
                    msgid = message.id
                    if isinstance(msgid, (list, tuple)):
                        msgid = msgid[0]
                    jscatalog[msgid] = message.string

            outfile = open(js_file, 'wb')
            try:
                json.dump(dict(
                    messages=jscatalog,
                    plural_expr=catalog.plural_expr,
                    locale=str(catalog.locale)
                    ), outfile)
            finally:
                outfile.close()
