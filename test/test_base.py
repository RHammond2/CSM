from itertools import product

import pytest
from attrs import define, field, fields, fields_dict, validators
from attr._make import _CountingAttr

from csm.models.base import AVAILABLE_MODELS, FieldsMeta
from csm import Land2015NLR, Land2020NLR, Land2021NLR


@pytest.mark.unit
def test_registry():
    """Test that AVAILABLE_MODELS is updated for models that have @register applied."""
    expected_availability = {
        "Land2015NLR": Land2015NLR,
        "Land2020NLR": Land2020NLR,
        "Land2021NLR": Land2021NLR,
    }
    assert len(AVAILABLE_MODELS) == len(expected_availability)
    for name, model in AVAILABLE_MODELS.items():
        assert model.__name__ == expected_availability[name].__name__


@define
class Demo(metaclass=FieldsMeta):
    a: int = field()
    b: str = field(default=12, converter=str, validator=validators.instance_of(str))
    c: float = field(default=1.23, init=False)

@pytest.mark.unit
def test_FieldsMeta():
    """Test that ``FieldsMeta`` provides ``attrs.fields`` and ``attrs.fields_dict``."""
    assert Demo.fields == fields(Demo)
    assert Demo.fields_dict == fields_dict(Demo)
