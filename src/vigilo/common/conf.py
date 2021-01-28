# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2021 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
A django-inspired settings module.

Use dictionary access on the 'settings' object.
Define VIGILO_SETTINGS in the environment to a valid file path
that will be imported.

The default file name is "settings.py".

To load the default config file::
    from vigilo.common.conf import settings
    settings.load_module()
    conntype = settings['MEMCACHE_CONN_TYPE']

To load a module-specific config file::
    from vigilo.common.conf import settings
    settings.load_module('vigilo.correlator')
    conntype = settings['MEMCACHE_CONN_TYPE']

By loading a module, the filename will be looked for in a subdirectory
named after the module. Examples:

C{settings.load_module()} looks for:
  - /etc/vigilo/settings.py
  - ~/.vigilo/settings.py
  - ./settings.py

C{settings.load_module("vigilo.connector")} looks for:
  - /etc/vigilo/connector/settings.py
  - ~/.vigilo/connector/settings.py
  - ./connector/settings.py

If you define VIGILO_SETTINGS to a valid filename, it will override the
search mechanism and be used instead.

Command-line usage::
    conntype=$(python -m vigilo.common.conf --get MEMCACHE_CONN_TYPE)

We can't import any other Vigilo code here.
This is because Vigilo code may log or require settings for some other reason.
"""

from __future__ import absolute_import, print_function

import os
import sys
import os.path
import glob

import pkg_resources

from configobj import ConfigObj, ParseError
from validate import Validator

from vigilo.common.gettext import translate
_ = translate(__name__)


__all__ = ( 'settings', )

# pylint: disable-msg=C0103

class ConfigParseError(ParseError):
    """
    Exception utilisée lorsqu'une erreur se produit au chargement
    d'un fichier de configuration de Vigilo.
    Elle est similaire à l'erreur C{ParseError} de C{ConfigObj},
    mais affiche en plus le nom du fichier analysé qui a provoqué
    l'erreur.
    """

    def __init__(self, ex, filename):
        """Initialisation de l'exception."""
        self.ex = ex
        self.filename = filename
        super(ConfigParseError, self).__init__(*ex.args)

    def __str__(self):
        """
        Affichage de l'exception.
        On ajoute simplement le nom du fichier qui a provoqué l'erreur.
        """
        return '%s (file being parsed: %s)' % (self.ex, self.filename)

# W0212: Access to a protected member FOO of a client class
# pylint: disable-msg=W0212
class _SectionWrapper(object):
    """
    Un wrapper autour de l'attribut _sectionmarker de la classe
    configobj.ConfigObj permettant de conserver la trace du nom
    de la section en cours de lecture.
    """

    def __init__(self):
        """Initialisation"""
        self._pattern = ConfigObj._sectionmarker
        self.section_name = None

    def match(self, *args, **kwargs):
        """
        Applique le motif régulier et retourne un objet contenant
        les correspondances éventuellement trouvées.
        """
        res = self._pattern.match(*args, **kwargs)
        if res is not None:
            self.section_name = None
            # res est de la forme :
            # (indent, sect_open, sect_name, sect_close, comment)
            (sect_open, sect_name, sect_close) = res.groups()[1:-1]
            depth = sect_open.count('[')
            if depth == 1 and sect_close.count(']') == depth:
                self.section_name = sect_name
        return res

# W0212: Access to a protected member FOO of a client class
# pylint: disable-msg=W0212
class _KeywordWrapper(object):
    """
    Un wrapper autour de l'attribut _keyword de la classe
    configobj.ConfigObj permettant de conserver la trace
    du nom de la clé en cours de lecture.
    """

    def __init__(self):
        """Initialisation"""
        self._pattern = ConfigObj._keyword
        self.key_name = None

    def match(self, *args, **kwargs):
        """
        Applique le motif régulier et retourne un objet contenant
        les correspondances éventuellement trouvées.
        """
        self.key_name = None
        res = self._pattern.match(*args, **kwargs)
        if res is not None:
            # res est de la forme (indent, key, value)
            self.key_name = res.groups()[1]
        return res

class VigiloConfigObj(ConfigObj):
    """
    Une classe permettant de gérer la configuration de Vigilo.
    Il s'agit d'une surcouche pour ConfigObj qui facilite juste
    le chargement de fichiers de configuration complémentaires.

    ATTENTION::
        pour le moment, ConfigObj n'accepte que le caractère '#'
        pour commencer une ligne de commentaire.
        Voir à ce propos le ticket ouvert sur leur tracker :
        http://code.google.com/p/configobj/issues/detail?id=19
    """

    paths = [
        '/etc/vigilo/%s',
        '~/.vigilo/%s',
        './%s',
    ]
    filenames = []

    # Wrappers autour de ConfigObj pour désactiver la détection des listes
    # pour la clé "args" dans la configuration d'un handler.
    _sectionmarker = _SectionWrapper()
    _keyword = _KeywordWrapper()

    def load_file(self, filename):
        """
        Charge un fichier de configuration
        """
        if filename in self.filenames:
            return # Double appel à load_file, ou boucle d'include

        configspec = filename[:-4] + '.spec'
        try:
            if os.path.exists(configspec):
                config = VigiloConfigObj(filename, file_error=True,
                    raise_errors=True, configspec=configspec,
                    interpolation=False)

                validator = Validator()
                valid = config.validate(validator)
                if not valid:
                    raise SyntaxError('Invalid value in configuration')

            else:
                config = VigiloConfigObj(filename, file_error=True,
                    raise_errors=True, interpolation=False)
        except IOError:
            pass
        except ParseError as e:
            raise ConfigParseError(e, filename)
        else:
            self.filenames.append(filename)
            if "include" in config.sections:
                includes = config["include"].as_list("include")
                for include in includes:
                    if not include:
                        # cas d'une valeur vide que le as_list traduit en ['']
                        continue
                    if not os.path.exists(include):
                        print("Can't find included file: %s" % include)
                        continue
                    if os.path.isdir(include):
                        # On inclut tous les fichiers INI du dossier pointé
                        # par le motif dans "include" (par ordre alphabétique).
                        # Les valeurs s'ajoutent, mais en cas de doublon,
                        # les valeurs du dernier fichier chargé écrasent
                        # celles des fichiers précédemment chargés.
                        included_files = glob.glob(os.path.join(
                                                   include, '*.ini'))
                        included_files.sort()
                        for included_file in included_files:
                            self.load_file(included_file)
                    else:
                        self.load_file(include)
            self.merge(config)

    def load_module(self, module=None, basename="settings.ini"):
        """
        Charge le fichier de configuration spécifique à un module
        de Vigilo.

        Usage::
            from vigilo.common.conf import settings
            settings.load_module(__name__)
        """
        filenames = []

        paths = [path % basename for path in self.paths]
        filenames.extend(paths)

        if module:
            module_components = module.split(".")
            if module_components[0] == "vigilo":
                del module_components[0]
            if len(module_components) > 0:
                filename = os.path.join(
                    module_components[0].replace("_", "-"),
                    basename)
                paths = [path % filename for path in self.paths]
                filenames.extend(paths)

        # Si la variable VIGILO_SETTINGS a été définie,
        # on utilise le chemin d'accès qu'elle contient.
        env_file = os.environ.get('VIGILO_SETTINGS', None)
        if env_file:
            filenames.append(env_file)

        for filename in filenames:
            filename = os.path.expanduser(filename)
            if not os.path.exists(filename):
                continue
            self.load_file(filename)
        if not self.filenames:
            import logging as temp_logging

            logger = temp_logging.getLogger(__name__)

            from logging.handlers import SysLogHandler
            logger.addHandler(SysLogHandler(
                address="/dev/log", facility='daemon'))
            logger.error(_("No configuration file found"))
            raise IOError(_("No configuration file found"))

    def reset(self):
        super(VigiloConfigObj, self).reset()
        self.filenames = []

    def reload(self):
        previous_filenames = self.filenames[:]
        self.reset()
        for filename in previous_filenames:
            self.load_file(filename)

    # pylint: disable-msg=W0201
    # W0201: Attribute 'foo' defined outside __init__
    # self.list_values est défini dans ConfigObj._initialise.
    def _handle_value(self, value):
        """
        Désactive la détection des listes pour le paramètre
        "args" des ""handler_*" dans la configuration des logs.
        """
        section = self._sectionmarker.section_name
        key = self._keyword.key_name
        temp_list_values = self.list_values
        if section is not None:
            if (section.startswith('handler_') and key == "args") or \
                (section.startswith('formatter_') and
                key in ("format", "datefmt")):
                self.list_values = False
        res = super(VigiloConfigObj, self)._handle_value(value)
        self.list_values = temp_list_values
        return res


settings = VigiloConfigObj(None, file_error=True, raise_errors=True,
                           interpolation=False)


def log_initialized(silent_load=False):
    """
    Cette fonction est appelée une fois la configuration chargée
    afin d'indiquer le nom du fichier qui a été chargé.
    """
    if silent_load:
        return
    from vigilo.common.logging import get_logger
    LOGGER = get_logger(__name__)
    LOGGER.debug('Loaded settings from paths: %s',
                 ", ".join(settings.filenames))


def setup_plugins_path(plugins_path):
    """Très fortement inspiré de Trac"""
    from vigilo.common.logging import get_logger
    LOGGER = get_logger(__name__)
    LOGGER.debug("Loading plugins from %s" % plugins_path)

    distributions, errors = pkg_resources.working_set.find_plugins(
        pkg_resources.Environment([plugins_path])
    )
    for dist in distributions:
        if dist in pkg_resources.working_set:
            continue
        LOGGER.debug('Adding plugin %(plugin)s from %(location)s', {
            'plugin': dist,
            'location': dist.location,
        })
        pkg_resources.working_set.add(dist)

    def _log_error(item, e):
        if isinstance(e, pkg_resources.DistributionNotFound):
            LOGGER.debug('Skipping "%(item)s": ("%(module)s" not found)', {
                'item': item,
                'module': e,
            })
        elif isinstance(e, pkg_resources.VersionConflict):
            LOGGER.error(_('Skipping "%(item)s": (version conflict '
                           '"%(error)s")'),
                         {'item': item, 'error': e})
        elif isinstance(e, pkg_resources.UnknownExtra):
            LOGGER.error(_('Skipping "%(item)s": (unknown extra "%(error)s")'),
                         {'item': item, 'error': e })
        elif isinstance(e, ImportError):
            LOGGER.error(_('Skipping "%(item)s": (can\'t import "%(error)s")'),
                         {'item': item, 'error': e })
        else:
            LOGGER.error(_('Skipping "%(item)s": (error "%(error)s")'), {
                'item': item,
                'error': e,
            })

    for dist, e in errors.iteritems():
        _log_error(dist, e)


def main():
    """
    Cette fonction est appelée lorsqu'un utilisateur lance la commande
    'vigilo-config'.
    Cet utilitaire permet d'obtenir la valeur d'un paramètre.
    """
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option('-s', '--section', dest='section')
    parser.add_option('-g', '--get', dest='get', metavar='SETTING_NAME')
    opts, args = parser.parse_args()
    if opts.get is None or opts.section is None:
        return 2
    try:
        for arg in args:
            if not os.path.exists(arg):
                print(_("No such file: %s") % arg)
                return 3
            settings.load_file(arg)
        if not args:
            settings.load_module()
    except ConfigParseError as e:
        print(e, file=sys.stderr)
        return 4
    if opts.section not in settings:
        print(_("No such section: %s") % opts.section, file=sys.stderr)
        return 1
    if opts.get not in settings[opts.section]:
        print(_("No such key: %s") % opts.get, file=sys.stderr)
        return 1
    val = settings[opts.section][opts.get]
    sys.stdout.write('%s\n' % val)
    return 0

if __name__ == '__main__':
    sys.exit(main())
