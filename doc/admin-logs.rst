Configuration des journaux
==========================

VigiConf est capable de transmettre un certain nombre d'informations au cours
de son fonctionnement à un mécanisme de journalisation des événements (par
exemple, des journaux systèmes, une trace dans un fichier, un enregistrement
des événements en base de données, etc.).

La syntaxe de la configuration des journaux est la même que pour le reste
de la configuration. Les mécanismes utilisés pour gérer les journaux sont
ceux mis à disposition par le module ``logging`` de Python.

Le reste de cette chapitre présente les informations basiques concernant
la configuration des journaux.
La documentation complète du format de configuration est disponible à l'adresse
http://docs.python.org/library/logging.html#configuration-file-format

La configuration de la journalisation se fait en manipulant
trois types d'objets :

-   les ``loggers``, qui permettent de configurer les modules python qui devront
    être journalisés et de définir les gestionnaires d'événements à appliquer ;
-   les ``handlers`` (gestionnaires d'événements), qui indiquent le traitement
    qui doit être appliqué aux événements reçus (enregistrement dans un
    fichier, dans les journaux Syslog du système, stockage en base de données,
    etc.) ;
-   les ``formatters``, qui permettent de configurer le formatage appliqué
    aux événements.

Les sections qui suivent vous donnent des informations sur la configuration
de chacun de ces éléments.


Configuration des ``loggers``
-----------------------------
Les loggers permettent d'indiquer les sources d'événements pour lesquelles
les événements de journalisation seront effectivement consignés.
Ils permettent également de définir les traitements qui seront appliqués
à ces événements (pour définir par exemple la destination des événements).

La configuration des loggers se fait en deux étapes :

- dans un premier temps, les loggers sont déclarés,
- puis, les loggers déclarés sont configurés.

Déclaration d'un ``logger``
^^^^^^^^^^^^^^^^^^^^^^^^^^^
La déclaration des loggers se fait sous la forme d'une liste des noms
des loggers, contenue sous la clé « keys » de la section « loggers ».

Les loggers sont organisés sous une forme hiérarchique, qui suit l'organisation
des modules Python sur le disque dur. Si aucun logger n'est défini pour traiter
les messages d'un module, le logger défini sur le niveau supérieur est utilisé.
L'arborescence du système de fichiers est ainsi parcourue jusqu'à ce qu'un
``logger`` intercepte le message ou qu'on ne puisse plus remonter.

Si aucun ``logger`` n'est trouvé après le parcours de la hiérarchie, un message
d'avertissement est affiché sur la console afin d'inciter l'utilisateur
à configurer correctement les journaux.

Par ailleurs, un ``logger`` spécial est défini qui apparaît toujours au sommet
de la hiérarchie des loggers, nommé « root ».

Exemple de parcours de la hiérarchie des loggers :

Si le module Python ``vigilo.common.conf`` émet un événement
et qu'aucun logger n'est associé à ce module, le gestionnaire de journaux
recherche un logger pour le module ``vigilo.common``. S'il n'en trouve pas,
il recherche un logger pour le module ``vigilo``.
Si après toutes ces recherches il n'en trouve toujours pas,
il recherche le logger ``root``.

Configuration d'un ``logger``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Chaque logger déclaré doit ensuite être configuré. La configuration d'un logger
appelé ``<nom_du_logger>`` se fait en ajoutant une section appelée
``logger_<nom_du_logger>`` dans le fichier de configuration.

Pour chaque logger, les clés suivantes sont configurables :

-   ``level`` (obligatoire) : niveau de criticité à partir duquel les messages
    seront pris en compte. Les niveaux utilisables sont (par ordre de criticité
    croissante) :

    *   NOTSET pour que l'événement soit toujours pris en compte,
        quelle que soit sa criticité,

    *   DEBUG pour ne prendre en compte que les événements
        au niveau « débogage » ou supérieur,

    *   INFO pour ne prendre en compte que les événements
        au niveau « information » ou supérieur,

    *   WARNING pour ne prendre en compte que les événements
        au niveau « avertissement » ou supérieur,

    *   ERROR pour ne prendre en compte que les événements
        au niveau « erreur » ou supérieur,

    *   CRITICAL pour ne prendre en compte que les événements
        au niveau « critique ».

-   ``qualname`` optionnel le nom du module Python qui sert de source
    pour les événements enregistrés par ce logger. Si ce champ est omis,
    c'est que le logger se trouve au sommet de la hiérarchie, et donc,
    qu'il s'agit du logger « root ».

-   ``propagate`` optionnel un entier qui indique si l'événement
    doit être propagé (1) aux loggers situés « au-dessus » dans
    la hiérarchie ou non (0). Par défaut, les messages sont propagés.

-   ``handlers`` obligatoire une liste contenant les noms des handlers gestionnaires d'événements qui traiteront les événements capturés par ce logger.


Exemple de configuration d'un ``logger``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
L'encadré suivant présente un exemple de configuration d'un ``logger``
nommé « log ». Cet exemple suppose par ailleurs qu'un ``handler`` « hand »
a été défini dans la configuration.

..  sourcecode:: ini

    [loggers]
    keys=log

    [logger_log]
    level=WARNING
    qualname=vigilo
    handlers=hand

Ce logger intercepterait tous les événements émis par un composant de Vigilo
et les enverrait au handler « hand » pour qu'ils soient traités.


Configurations des ``handlers`` (gestionnaires d'événements)
------------------------------------------------------------
Les handlers permettent d'indiquer comment sont traités les événements reçus.
Ils permettent par exemple d'indiquer que les messages doivent être stockés
dans une base de données, dans les journaux systèmes, envoyés par email, etc.

La configuration des handlers se fait en deux étapes :

- dans un premier temps, les handlers sont déclarés,
- puis, les handlers déclarés sont configurés.

Déclaration d'un ``handler``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
La déclaration des handlers se fait sous la forme d'une liste des noms
des handlers, contenue sous la clé « keys » de la section « handlers ».

Configuration d'un ``handler``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Chaque handler déclaré doit ensuite être configuré. La configuration
d'un handler appelé <nom_du_handler> se fait en ajoutant une section
appelée « handler_<nom_du_handler> » dans le fichier de configuration.

Pour chaque handler, les clés suivantes sont configurables :

-   ``class`` (obligatoire) : la classe Python qui effectuera le stockage
    des messages. Les plus couramment utilisées sont « handlers.SysLogHandler »
    (enregistrement vers les journaux systèmes de Linux),
    « StreamHandler » (enregistrement dans un flux, comme par exemple
    la sortie standard du programme).
    La liste complète des handlers utilisables est disponible sur
    http://docs.python.org/library/logging.html

-   ``args`` (optionnel) : arguments qui seront passés au constructeur
    de la classe désignée par la clé ``class``.

-   ``level`` (obligatoire) : le niveau de criticité à partir duquel
    les messages seront pris en compte. Les niveaux utilisables
    sont les mêmes que pour les loggers.

-   ``formatter`` (obligatoire) : le nom du ``formatter`` à utiliser
    pour mettre en forme les messages.

Exemple de configuration d'un ``handler``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
L'encadré suivant présente un exemple de configuration d'un handler
nommé « hand ». Cet exemple suppose par ailleurs qu'un ``formatter`` « fmt »
a été défini dans la configuration.

..  sourcecode:: ini

    [handlers]
    keys=hand

    [handler_hand]
    class=handlers.SysLogHandler
    args='/dev/log', 'daemon'
    level=NOTSET
    formatter=fmt

Ce handler enregistre les événements dans le journal du système,
quelque soit leur niveau de criticité, en utilisant le ``formatter`` « fmt ».


Configuration des ``formatters``
--------------------------------
Les formatters permettent de mettre en forme les messages avant leur stockage.
La configuration des formatters se fait en deux étapes :

- dans un premier temps, les formatters sont déclarés,
- puis, les formatters déclarés sont configurés.

Déclaration d'un ``formatter``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
La déclaration des formatters se fait sous la forme d'une liste des noms
des formatters, contenue sous la clé « keys » de la section « formatters ».

Configuration d'un ``formatter``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Chaque formatter déclaré doit ensuite être configuré. La configuration
d'un formatter appelé <nom_du_formatter> se fait en ajoutant une section
appelée «formatter_<nom_du_formatter> » dans le fichier de configuration.

Pour chaque formatter, les clés suivantes sont configurables :

-   ``format`` (obligatoire) : un texte qui décrit la mise en forme du message.
    Ce texte peut faire références à des informations contextuelles concernant
    l'événement à enregistrer. Ces informations contextuelles sont insérées
    en utilisant le mécanisme de formatage des chaines de caractères de Python.
    Par exemple, le message original de l'événement peut être inséré
    dans le texte qui sera effectivement enregistré à l'aide de la
    substitution suivante ::

        %(message)s

    La liste des informations contextuelles les plus fréquemment utilisées
    est fournie dans la suite de ce document. La liste complète peut être
    consultée en lisant la documentation de Python concernant le module
    ``logging``.

-   ``datefmt`` (optionnel) : un texte indiquant le format à utiliser
    pour les dates. La description complète du format est présentée
    dans la documentation de Python
    (http://docs.python.org/library/time.html#time.strftime).
    Par défaut, le format ISO 8601 est utilisé.


Informations contextuelles disponibles pour les ``formatters``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Plusieurs informations contextuelles peuvent être insérées automatiquement
par les formatters avant l'envoi d'un message dans les journaux.

Les informations contextuelles suivantes sont disponibles :

-   La date à laquelle l'événement est survenu peut être insérée,
    dans un format intelligible, grâce à la substitution suivante ::

        %(asctime)s

-   La criticité du message reçu (DEBUG, WARNING, ERROR, etc.) peut être
    insérée sous forme textuelle grâce à la substitution suivante ::

        %(levelname)s

-   Le nom du module qui a émis le message peut être inséré grâce à cette
    substitution ::

        %(module)s

-   Le message original associé à l'événement peut être inséré grâce à cette
    substitution ::

        %(message)s

Cette liste ne contient que les informations les plus couramment utilisées.
La liste complète est disponible sur
http://docs.python.org/library/logging.html#formatter.

Exemple de configuration d'un ``formatter``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
L'encadré suivant présente un exemple de configuration d'un formatter
nommé « fmt ».

..  sourcecode:: ini

    [formatters]
    keys=fmt

    [formatter_fmt]
    format=[%(asctime)s] %(levelname)s – %(message)s
    datefmt=%a, %d %b %Y %H:%M:%S

Ce formateur affiche le niveau de criticité (sous forme textuelle) ainsi que
le message de l'événement original. Le message est précédé de la date.

Un exemple de message enregistré en utilisant ce formateur serait ::

    [Thu, 28 Jun 2001 14:17:15] ERROR – Could not connect to memcached.


Exemple de configuration complète des journaux
----------------------------------------------
L'encadré qui suit donne un exemple simple mais complet d'une configuration
des journaux dans le cas du corrélateur de Vigilo. Le résultat de cette
configuration est ensuite détaillé.

..  sourcecode:: ini

    [loggers]
    keys = root,rules

    [handlers]
    keys = syslog

    [formatters]
    keys = generic

    [logger_root]
    level = WARNING
    handlers = syslog

    [logger_rules]
    level = INFO
    handlers = syslog
    qualname = vigilo.correlator.rules

    [handler_syslog]
    class=handlers.SysLogHandler
    level=DEBUG
    formatter=nullFormatter
    args='/dev/log', 'daemon'

    [formatter_generic]
    format = %(message)s
    datefmt =

Dans cette configuration, tous les messages émis par le corrélateur
et qui ont un niveau de criticité au moins équivalent à « WARNING »
sont enregistrés dans les journaux du système (syslog).

Par ailleurs, les messages issus des règles de corrélation
(module Python ``vigilo.correlator.rules``) sont consignés
dès lors que leur niveau de criticité est supérieur ou égal à « INFO ».

Le message enregistré a un formatage « brut » où seul le message apparaît.
En effet, dans le cas d'un handler de type « handlers.SysLogHandler »,
il n'est pas nécessaire d'ajouter des informations supplémentaires
(nom et PID du processus qui a envoyé l'événement, heure où l'événement
a été consigné, etc.). Le système ajoute automatiquement ces informations
à l'événement.


.. vim: set tw=79 :
