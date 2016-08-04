Vigilo Common
=============

La bibliothèque "common" regroupe les fonctions transverses à Vigilo_,
notamment le chargement de fichiers de configuration, la journalisation,
l'internationalisation, etc.


Dépendances
-----------
Vigilo nécessite une version de Python supérieure ou égale à 2.5. Le chemin de
l'exécutable python peut être passé en paramètre du ``make install`` de la
façon suivante::

    make install PYTHON=/usr/bin/python2.6

La bibliothèque "common" a besoin des modules python suivants :

- Babel >= 0.9.4
- setuptools (ou distribute)
- configobj (à patcher)
- networkx

Un patch est nécessaire pour le module configobj, il se trouve dans le dossier
"patches" (il a été remonté au projet).


Installation
------------
L'installation se fait par la commande ``make install`` (à exécuter en
``root``).


License
-------
Vigilo Common est sous licence `GPL v2`_.

.. _Vigilo: http://www.projet-vigilo.org
.. _GPL v2: http://www.gnu.org/licenses/gpl-2.0.html

.. vim: set syntax=rst fileencoding=utf-8 tw=78 :
