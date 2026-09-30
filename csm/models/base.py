"""Provides the ``AVAILABLE_MODELS`` model registry and ``FieldsMeta`` for quick-access
``attrs.fields`` data available.
"""

AVAILABLE_MODELS = {}

def register(name):
    """Register a class and its string name in ``AVAILABLE_MODELS``."""
    def make_available(cls):
        AVAILABLE_MODELS[name] = cls
        return cls
    return make_available


class FieldsMeta(type):
    """Metaclass providing the :py:attr:`fields` and :py:attr:`fields_dict` as class properties."""
    @property
    def fields(cls):
        """Enables ``Model.fields`` in place of ``attrs.fields(Model)`` for easy of attribute data
        getting.
        """
        return cls.__attrs_attrs__

    @property
    def fields_dict(cls):
        """Enables ``Model.fields_dict`` in place of ``attrs.fields_dict(Model)`` for easy of
        attribute data getting.
        """
        return {el.name: el for el in cls.__attrs_attrs__}