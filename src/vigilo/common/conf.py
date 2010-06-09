# vim: set fileencoding=utf-8 sw=4 ts=4 et :
"""
A django-inspired settings module.

Use dictionary access on the 'settings' object.
Define VIGILO_SETTINGS in the environment to a valid file path
that will be imported.

The settings file will be searched in a list of directories defined in
the L{Settings._dirs} list.

The default file name is "settings.py", and the first valid file is returned.

To load the default config file::
    from vigilo.common.conf import settings
    conntype = settings['MEMCACHE_CONN_TYPE']

To load a module-specific config file::
    from vigilo.common.conf import settings
    settings.load("connector")

By loading a module, the filename will be looked for in a subdirectory
named after the module. Examples:

C{settings.load()} looks for:
  - /etc/vigilo/settings.py
  - ~/.vigilo/settings.py
  - ./settings.py

C{settings.load("connector")} looks for:
  - /etc/vigilo/connector/settings.py
  - ~/.vigilo/connector/settings.py
  - ./connector/settings.py

If you define VIGILO_SETTINGS to a valid filename, it will override the
search mechanism and be used instead.

Command-line usage::
    conntype=$(python -m vigilo.common.conf --get MEMCACHE_CONN_TYPE)


Impl notes::
    a ConfigParser.SafeConfigParser would have worked as well,
    we'd replace settings.py in PYTHONPATH with a settings.cfg in PWD.
    I guess I'm too used to django.

We can't import any other Vigilo code here.
This is because Vigilo code may log or require settings for some other reason.
"""

from __future__ import absolute_import

import os
import sys
import os.path
from configobj import ConfigObj, ParseError
from validate import Validator

__all__ = ( 'settings', )


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
        super(ConfigParseError, self).__init__(
            ex.message, ex.line_number, ex.line)

    def __str__(self):
        """
        Affichage de l'exception.
        On ajoute simplement le nom du fichier qui a provoqué l'erreur.
        """
        return '%s (file being parsed: %s)' % (self.ex, self.filename)

class VigiloConfigObj(ConfigObj):
    """
    Une classe permettant de gérer la configuration de Vigilo.
    Il s'agit d'une surcouche pour ConfigObj qui facilite juste
    le chargement de fichiers de configuration complémentaires.

    ATTENTION : pour le moment, ConfigObj n'accepte que le caractère '#'
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

    def load_file(self, filename):
        """
        Charge un fichier de configuration
        """
        try:
            configspec = filename[:-4] + '.spec'
            if os.path.exists(configspec):
                config = VigiloConfigObj(filename, file_error=True,
                    raise_errors=True, configspec=configspec,
                    interpolation=False)

                validator = Validator()
                valid = config.validate(validator)
                if not valid:
                    raise SyntaxError, 'Invalid value in configuration'

            else:
                config = VigiloConfigObj(filename, file_error=True,
                    raise_errors=True, interpolation=False)
        except IOError:
            pass
        except ParseError, e:
            raise ConfigParseError(e, filename)
        else:
            #print "Found '%s', merging." % filename
            self.merge(config)
            self.filenames.append(filename)

    def load_module(self, module=None):
        """
        Charge le fichier de configuration spécifique à un module
        de Vigilo.

        Usage:
            from vigilo.common.conf import settings
            settings.load_module(__name__)
        """
        filenames = []

        paths = [path % "settings.ini" for path in self.paths]
        filenames.extend(paths)

        if module:
            module_components = module.split(".")
            if module_components[0] == "vigilo":
                del module_components[0]
            if len(module_components) > 0:
                filename = "%s/settings.ini" % \
                    module_components[0].replace("_", "-")
                paths = [path % filename for path in self.paths]
                filenames.extend(paths)

        # Si la variable VIGILO_SETTINGS a été définie,
        # on utilise le chemin d'accès qu'elle contient.
        env_file = os.environ.get('VIGILO_SETTINGS', None)
        if env_file:
            filenames.append(env_file)

        #print filenames
        for filename in filenames:
            filename = os.path.expanduser(filename)
            if not os.path.exists(filename):
                #print "Not found:", filename
                continue
            self.load_file(filename)
        if not self.filenames:
            from vigilo.common.gettext import translate
            import logging as temp_logging

            _ = translate(__name__)
            logger = temp_logging.getLogger(__name__)

            from logging.handlers import SysLogHandler
            logger.addHandler(SysLogHandler(
                address="/dev/log", facility='daemon'))
            logger.error(_("No configuration file found"))
            raise IOError(_("No configuration file found"))


settings = VigiloConfigObj(None, file_error=True, raise_errors=True,
                            interpolation=False)


def log_initialized():
    """
    Cette fonction est appelée une fois la configuration chargée
    afin d'indiquer le nom du fichier qui a été chargé.
    """

    from vigilo.common.logging import get_logger
    LOGGER = get_logger(__name__)
    LOGGER.info('Loaded settings from paths: %s', ", ".join(settings.filenames))

def main(*args):
    """
    Cette fonction est appelée lorsqu'un utilisateur lance la commande
    'vigilo-config'.
    Cet utilitaire permet d'obtenir la valeur d'un paramètre.
    """
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option('-s', '--section', dest='section')
    parser.add_option('-g', '--get', dest='get', metavar='SETTING_NAME')
    opts = parser.parse_args()[0]
    if opts.get is None or opts.section is None:
        return -2
    settings.load_module()
    val = settings[opts.section][opts.get]
    sys.stdout.write('%s\n' % val)
    return 0

if __name__ == '__main__':
    sys.exit(main())

