#!/usr/bin/env python
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2021 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

import os, sys
from setuptools import setup, find_packages

try:
    from distutils.command.build import build as orig_build
except ImportError:
    cmdclass = {}
else:
    class build(orig_build):
        def has_i18n(self):
            return getattr(self.distribution, 'message_extractors', None)

        sub_commands = orig_build.sub_commands + [
            ('compile_catalog', has_i18n),
        ]
    cmdclass = {'build': build}


tests_require = [
    'coverage',
    'nose',
    'pylint',
]

def install_i18n(i18ndir, destdir):
    data_files = []
    langs = []
    for f in os.listdir(i18ndir):
        if os.path.isdir(os.path.join(i18ndir, f)) and not f.startswith("."):
            langs.append(f)
    for lang in langs:
        for f in os.listdir(os.path.join(i18ndir, lang, "LC_MESSAGES")):
            if f.endswith(".mo"):
                data_files.append(
                        (os.path.join(destdir, lang, "LC_MESSAGES"),
                         [os.path.join(i18ndir, lang, "LC_MESSAGES", f)])
                )
    return data_files

setup(name='vigilo-common',
        version='5.2.0',
        author='Vigilo Team',
        author_email='contact.vigilo@csgroup.eu',
        url='https://www.vigilo-nms.com/',
        description="Vigilo common library",
        license='http://www.gnu.org/licenses/gpl-2.0.html',
        long_description="This library provides common facilities to Vigilo "
                         "components, such as configuration loading, "
                         "logging, daemonizing, i18n, etc.",
        install_requires=[
            'Babel >= 0.9.4',
            'setuptools',
            'configobj',
            'networkx',
            ],
        extras_require={
            'tests': tests_require,
            },
        test_suite='nose.collector',
        namespace_packages = [
            'vigilo',
            ],
        packages=find_packages("src"),
        message_extractors={
            'src': [
                ('**.py', 'python', None),
            ],
        },
        entry_points={
            'console_scripts': [
                'vigilo-config = vigilo.common.conf:main',
                'vigilo-plugins = vigilo.common.plugins:main',
            ],
            'distutils.commands': [
                'identity_catalog = vigilo.common.commands:identity_catalog',
                'compile_catalog_js = vigilo.common.commands:compile_catalog_plusjs',
            ],
            'distutils.setup_keywords': [
                'vigilo_build_vars = vigilo.common.commands:validate_build_vars',
            ],
        },
        package_dir={'': 'src'},
        cmdclass=cmdclass,
        data_files=install_i18n("i18n", os.path.join(sys.prefix, 'share', 'locale'))
        )
