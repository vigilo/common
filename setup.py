#!/usr/bin/env python
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
import os, sys
from setuptools import setup

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
        version='2.0.0',
        author='Vigilo Team',
        author_email='contact@projet-vigilo.org',
        url='http://www.projet-vigilo.org/',
        description='Common vigilo utilities',
        license='http://www.gnu.org/licenses/gpl-2.0.html',
        long_description='Common vigilo utilities\n'
        +'Currently configuration, logging, python backward compatibility.\n',
        install_requires=[
            'Babel >= 0.9.4',
            'setuptools',
            'configobj',
            ],
        extras_require={
            'tests': tests_require,
            },
        namespace_packages = [
            'vigilo',
            ],
        packages=[
            'vigilo',
            'vigilo.common',
            ],
        message_extractors={
            'src': [
                ('**.py', 'python', None),
            ],
        },
        entry_points={
            'console_scripts': [
                'vigilo-config = vigilo.common.conf:main',
                ],
            'distutils.commands': [
                'identity_catalog = vigilo.common.commands:identity_catalog',
                ],
            },
        package_dir={'': 'src'},
        data_files=install_i18n("i18n", os.path.join(sys.prefix, 'share', 'locale'))
        )

