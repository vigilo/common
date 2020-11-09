# -*- coding: utf-8 -*-
# Copyright (C) 2006-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Commandes supplémentaires pour setuptools.
"""
import re
import os
import stat
import sysconfig
from tempfile import mkstemp

from distutils import log
from distutils.cmd import Command
from distutils.command.install_data import install_data as orig_install_data
from distutils.errors import DistutilsOptionError

from babel import Locale
from babel.core import UnknownLocaleError
from babel.messages.pofile import read_po, write_po
from babel.messages.frontend import compile_catalog

try:
    from simplejson import dump
except ImportError:
    from json import dump


class install_data(orig_install_data):
    """
    Installe les fichiers du module contenant des données,
    tout en supportant des variables de substitution dans le chemin
    du dossier cible, ainsi que dans les fichiers eux-mêmes.
    """
    user_options = orig_install_data.user_options + [
        ('substitute=', None,
         "variables to substitute with their environment value"),
    ]

    def initialize_options(self):
        orig_install_data.initialize_options(self)
        self._replacements = {}
        self.substitute = ''
        self.subst_pat = None

        self.install_lib = None
        self.install_purelib = None
        self.install_platlib = None
        self.install_scripts = None
        self.install_headers = None

        self._sysconfig = {}
        for k in ('BINDIR', 'INCLUDEDIR', 'LIBDIR', 'MANDIR', 'SCRIPTDIR'):
            v = sysconfig.get_config_var(k)
            if v:
                self._sysconfig[k] = v

        self._internal_dirs = {
            'bindir': 'install_scripts',
            'datadir': 'install_dir',
            'includedir': 'install_headers',
            'libdir': 'install_lib',
            'platlibdir': 'install_platlib',
            'purelibdir': 'install_purelib',
        }

    def finalize_options(self):
        orig_install_data.finalize_options(self)
        self.set_undefined_options(
            'install',
            ('install_headers', 'install_headers'),
            ('install_lib', 'install_lib'),
            ('install_platlib', 'install_platlib'),
            ('install_purelib', 'install_purelib'),
            ('install_scripts', 'install_scripts'),
        )

        pattern = ['[A-Z_][A-Z0-9_]*']
        pattern.extend(self._internal_dirs)
        subname = re.compile('^(%s)$' % '|'.join(pattern))
        subst = self.substitute.replace(',', ' ').split()
        new_subst = set()
        for s in subst:
            if s[0] == '@' and s[-1] == '@':
                s = s[1:-1]
            if not subname.match(s):
                raise DistutilsOptionError(
                    'Substitutions names may only contain '
                    'the characters: A-Z, 0-9 and "_"')
            new_subst.add(s)
        if new_subst:
            self.subst_pat = re.compile(
                "@(%s)@" % '|'.join(reversed(sorted(new_subst))))

        data_files = []
        for f in self.data_files:
            if isinstance(f, str):
                data_files.append(self._subst_variables(f))
            else:
                data_files.append( (self._subst_variables(f[0]), f[1]) )
        self.data_files = data_files

    def _subst_replace(self, match):
        v = match.group(1)

        if v in self._internal_dirs:
            res = getattr(self, self._internal_dirs[v])

            if not self.root or not res.startswith(self.root):
                return res

            root = self.root
            if root.endswith(os.path.sep):
                root = root[:-len(os.path.sep)]

            res = res[len(root):]
            return res

        res = os.environ.get(v)
        if res is not None:
            return res

        res = self._sysconfig[v]
        return res

    def _subst_variables(self, content):
        if not self.subst_pat:
            return content
        return self.subst_pat.sub(self._subst_replace, content)

    def copy_file(self, infile, outfile, preserve_mode=1, preserve_times=1,
                  *args, **kwargs):
        basename = os.path.basename(infile)

        # If infile is not a template or is simply named ".in", copy it as-is.
        if basename == '.in' or not basename.endswith('.in'):
            return orig_install_data.copy_file(
                self, infile, outfile, preserve_mode, preserve_times,
                *args, **kwargs)

        # Copy the content of the original file to a temporary one,
        # while doing the variables' substitution on the fly.
        # Only small files (< 1 MB) should be used as templates,
        # since we are reading the whole file in memory here.
        try:
            (outfd, tmpfile) = mkstemp()
        except Exception:
            raise
        else:
            os.close(outfd) # The low-level API is unreliable in Python < 3.5
                            # when signals are received (see also PEP 475).
                            # We thus reopen the file using the high-level API.
            log.info("substituting variables from %(src)s into %(dest)s" %
                {'src': infile, 'dest': tmpfile})
            with open(tmpfile, 'wb') as outfd:
                with open(infile, 'rw') as infd:
                    outfd.write(self._subst_variables(infd.read(-1)))

            # Take care of preserve_* arguments (see distutils' code).
            if preserve_mode or preserve_times:
                st = os.stat(infile)
                if preserve_times:
                    os.utime(tmpfile, (st[stat.ST_ATIME], st[stat.ST_MTIME]))
                if preserve_mode:
                    os.chmod(tmpfile, stat.S_IMODE(st[stat.ST_MODE]))

            # Finally, copy the temporary file to its final destination.
            return orig_install_data.copy_file(
                self, tmpfile, os.path.join(outfile, basename[:-3]),
                preserve_mode, preserve_times, *args, **kwargs)
        finally:
            os.unlink(tmpfile)


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
                dump(dict(
                    messages=jscatalog,
                    plural_expr=catalog.plural_expr,
                    locale=str(catalog.locale)
                    ), outfile)
            finally:
                outfile.close()
