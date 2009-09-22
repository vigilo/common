#!/usr/bin/env python
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
from setuptools import setup

setup(name='vigilo-common',
        version='0.1',
        author='Gabriel de Perthuis',
        author_email='gabriel.de-perthuis@c-s.fr',
        url='http://www.projet-vigilo.org/',
        description='Common vigilo utilities',
        license='http://www.gnu.org/licenses/gpl-2.0.html',
        long_description='Common vigilo utilities\n'
        +'Currently configuration, logging, python backward compatibility.\n',
        install_requires=[
            'setuptools',
            ],
        namespace_packages = [
            'vigilo',
            ],
        packages=[
            'vigilo.common',
            ],
        entry_points={
            'console_scripts': [
                'vigilo-config = vigilo.common.conf:main',
                ],
            },
        package_dir={'': 'src'},
        )

