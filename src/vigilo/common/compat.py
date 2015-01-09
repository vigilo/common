# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2011-2015 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Compatiblity wrappers for pre-2.6 python.

Warning: monkey-patching.
"""
if not hasattr(property, 'setter'):
    class _property(property):
        """
        Redéfini la classe property native pour permettre
        le passage d'un getter, d'un setter, d'un deleter
        et de la documentation directement.
        """
        @property
        def setter(self):
            """Change la manière dont property est appliqué aux fonctions."""

            def decorate(func):
                """Décorateur pour modifier le comportement de property."""
                return property(
                        fget=self.fget,
                        fset=func,
                        fdel=self.fdel,
                        doc=self.__doc__)
            return decorate

    __builtins__['property'] = _property

