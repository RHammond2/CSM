"""Provides all the ``attrs``-based utilities for the CSM base model and its subclasses."""

from typing import Any
from functools import cache, partial

import numpy as np
import networkx as nx
from attrs import Attribute, field, converters, validators
from attr._make import attrib


VALID_SOURCES = ("NLR", )
VALID_YEARS = (2015, 2020, 2021)
VALID_BASIS = ("land", )
VALID_MODELS = ("2015LandNLR", "2020LandNLR", "2021LandNLR")


def make_name_variations(*, source: str = "NLR", basis: str = "land", year: int | str = 2015) -> tuple[str, ...]:
    """Creates a series of standard name patters that can be recognized from user inputs
    taking the following forms where :py:attr:`source` = "NLR", :py:attr:`basis` = "land",
    and :py:attr:`year` = 2015.

    Acceptable variations:
    
        - model class name: "Land2015NLR"
        - year-only: 2015 or "2015" (only accepted for 2015, 2020, and 2021)
        - source and year combinations (only accepted for 2015, 2020, and 2021) separated by a space
          or dash: "NLR-2015", "2015-NLR"
        - basis and year combinations separated by a space or dash: "land-2015", "2015-land"

    Args:
        source (str): The abbreviated name of the source, such as NLR. Currently only
            accepts "NLR".
        basis (str): Land-based, ("land"), fixed-bottom offshore wind ("fosw"), or floating offshore
            wind ("flosw"). Currently only accepts "land".
        year (int | str): The year of the model's basis. Must be one of 2015, 2020, or 2021.

    Returns:
        tuple: A tuple of name combinations as outlined in the description.
    """
    if source.upper() not in VALID_SOURCES:
        raise ValueError(f"'source' must be one of {VALID_SOURCES}, not: {source}")
    year = int(year)
    if int(year) not in VALID_YEARS:
        raise ValueError(f"'year' must be one of {VALID_YEARS}, not: {source}")
    if basis.lower() not in VALID_BASIS:
        raise ValueError(f"'basis' must be one of {VALID_BASIS}, not: {source}")

    variants = [str(year), int(year), f"{basis.title()}{year}{source.upper()}"]
    for sep in ("-", " "):
        variants.extend([f"{basis.lower()}{sep}{year}", f"{year}{sep}{basis.lower()}"])
        variants.extend([f"{source.lower()}{sep}{year}", f"{source.upper()}{sep}{year}"])
        variants.extend([f"{year}{sep}{source.lower()}", f"{year}{sep}{source.upper()}"])

    return variants



def convert_if_allowable_type(value: Any, target: type, allowable: type | tuple[type]) -> Any:
    """Converts the type of :py:attr:`value` to the :py:attr:`target` type if it is one of an
    :py:attr:`allowable` type. If :py:attr:`value` is already the correct type, or is not of an
    :py:attr:`allowable` type for conversion, the :py:attr:`value` will be returned unmodified.

    Args:
        value (Any): User input field value.
        target (type): The type the :py:attr:`value` should be converted to if it is not already
            of that type.
        allowable (type | tuple[type]): The allowable type(s) for conversion, i.e., ``(str, int)``
            for a target type of ``float``.

    Returns:
        Any: The original :py:attr:`value` or a converted :py:attr:`value` of type
        :py:attr:`target`.
    """
    if isinstance(value, target) or not isinstance(value, allowable):
        return value
    return target(value)


convert_float = partial(convert_if_allowable_type, target=float, allowable=(int, str))


def create_field(
    obj: type,
    units: str = "unitless",
    io_type: str = "input",
    *,
    default: int | float | bool | None = None,
    additional_validators: list[callable] | None = None,
    additional_converters: list[callable] | None = None,
    **kwargs,
) -> field:
    """Creates an :py:attr:`obj`-based field with pre-loaded defaults, conversions, validations,
    and metadata.

    Args:
        obj (type): A type. Currently only accepts ``int``, ``float``, or ``bool``.
        units (str, optional): OpenMDAO-compatible units. See
            <https://openmdao.org/newdocs/versions/latest/features/units.html> for more details.
            Defaults to "unitless".
        io_type (str, optional): One of "input", "output", or "both" for how the attribute should be
            initialized within a WISDEM model. Typically ``xx_mass` and ``xx_cost`` attributes
            are both inputs and outputs. Defaults to "input".
        default (int | float | bool, optional): Value of the default, if not None.
        additional_validators (list[callable], optional): A list of additional validator functions
            to attach to the ``attrs.field`` initialization. Defaults to None
        additional_converters (list[callable], optional): A list of additional converter functions
            to attach to the ``attrs.field`` initialization. Defaults to None
        kwargs (dict[str, Any], optional): Additional parameterizations to pass to ``attrs.field``.

    Returns:
        attrs.field:
            Creates an :py:attr:`attrs.field` object for the attribute.

    Raises:
        NotImplementedError:
            Raised if an unsupported type object is passed. Only ``int``, ``float``, and ``bool``
            are accepted at this time.
    """
    io_types = ("input", "output", "both")
    if not isinstance(io_type, str):
        raise TypeError("`io_type` must be a `str` and one of 'input', 'output', or 'both'.")
    io_type = io_type.lower()
    if io_type not in io_types:
        raise ValueError("`io_type` must be one of 'input', 'output', or 'both'.")

    _converters = None
    if additional_converters is not None:
        _converters = [converters.optional(el) for el in additional_converters]

    _validators = [validators.optional(validators.instance_of(obj))]
    if additional_validators is not None:
        _validators += [validators.optional(el) for el in additional_validators]

    if obj is int:
        pass
    elif obj is float:
        if _converters is None:
            _converters = []
        _converters = [converters.optional(convert_float), *_converters]
    elif obj is bool:
        if _converters is None:
            _converters = []
        _converters = [converters.optional(converters.to_bool), *_converters]
    else:
        raise NotImplementedError(f"No setup created for type: {obj}")

    _field = field(
        default=default,
        converter=_converters,
        validator=_validators,
        metadata={"units": units, "io": io_type},
        **kwargs,
    )
    return _field


def reuse(
    attribute: Attribute,
    *,
    default: Any = None,
    metadata: dict | None = None,
    init: bool | None = None,
) -> attrib:
    """Reuses an existing :py:attr:`attrs.Attribute` object with an updated default value.

    Borrowed idea from https://github.com/python-attrs/attrs/pull/1429 until the functionality
    is fully integrated.

    Args:
        attribute (:py:attr:`attrs.Attribute`): The attribute to modify.
        default (Any, optional): The new default value.
        metadata (None, optional): Updated metadata dictionary to change attributes such as
            "units" or "io". Defaults to None.
        init (bool | None): Custom value for the `init` attribute, if modification is desired. If
            None, then the existing value for the :py:attr:`attribute` will be used.
            Defaults to False.

    Returns:
        attrib: The new attribute object used in class initialization.
    """
    attribute_metadata = dict(attribute.metadata)
    attribute_metadata.update(metadata if metadata is not None else {})

    # NOTE: if adding factory, then only one of default or factory can be used.
    kwargs = {
        "default": attribute.default if default is None else default,
        "converter": attribute.converter,
        "validator": attribute.validator,
        "metadata": attribute_metadata,
        "repr": attribute.repr,
        "cmp": None,
        "hash": attribute.hash,
        "init": attribute.init if init is None else init,
        "type": attribute.type,
        "kw_only": attribute.kw_only,
        "eq": attribute.eq,
        "order": attribute.order,
        "on_setattr": attribute.on_setattr,
        "alias": attribute.alias,
    }
    return attrib(**kwargs)


Attribute.reuse = reuse


def generate_parameterization(parameterized_kwargs: dict) -> dict[str, list]:
    """Validates the kwargs to be parameterized and creates the full set of values to be used for
    each argument.

    Args:
        parameterized_kwargs (dict[str, int  |  float  |  bool]): Dictionary of independent
            variables with an iterable value consisting of an explicit set of values or range
            of values generated by ``np.linspace``. For both cases, the first value must be one
            of "inputs" or "range". Subsequent values should specified according to the case:

            - "inputs": all subsequent values will be used as inputs, e.g.,
                {"tower_length": ("inputs", 90, 100)} will run 2 iterations, one with a 90m tower
                length and one with a 100 meter tower length.
            - "range": subsequent values must be start, stop, num where stop is inclusive,
                e.g., {"efficiency_max": ("range", 0.8, 1.0, 5)} will run 5 iterations of the
                model varying ``efficiency_max`` with values 0.8, 0.85, 0.9, 0.95, and 1.0.

    Raises:
        ValueError: Raised if any of the keys of :py:attr:`parameterized_kwargs` are not defined
            as a "range" or "inputs" style variable.
        ValueError: Raised if fewer than 2 inputs are able to be generated by the
            parameterization type.

    Returns:
        dict[str, list]]: Dictionary of each argument and the full set of values to parameterize
            a model.
    """
    expanded = {}
    for name, vals in parameterized_kwargs.items():
        match how := vals[0]:
            case "inputs":
                _inputs = vals[1:]
            case "range":
                if len(vals[1:]) != 3:
                    msg = (
                        f"'range' input for '{name}' must have 3 values: start, stop, and"
                        " number of total values."
                    )
                    raise ValueError(msg)
                _min, _max, _num = vals[1:]
                _inputs = list(np.linspace(_min, _max, _num))
            case _:
                raise ValueError(
                    f"First value for '{name}' must be 'inputs' or 'range', not '{how}'."
                )
        if len(_inputs) < 2:
            raise ValueError(f"Parameterized inputs for '{name}' must have at least 2 values.")
        expanded[name] = _inputs
    return expanded


@cache
def get_dependent_attributes(parameter_graph: nx.DiGraph, name: str) -> set[str]:
    """Returns a set of model attributes that depend on the value of :py:attr:`name`.

    Args:
        parameter_graph (nx.DiGraph): The ``CSMBase.parameter_graph``.
        name (str): The name of a model attribute that a user inputs or can be
            calculated.

    Returns:
        set[str]: Set of model attribute names that rely on the value of :py:attr:`name`.
    """
    return nx.ancestors(parameter_graph, name)


@cache
def get_descendant_attributes(parameter_graph: nx.DiGraph, name: str) -> set[str]:
    """Returns a set of model attributes :py:attr:`name` requires.

    Args:
        parameter_graph (nx.DiGraph): The ``CSMBase.parameter_graph``.
        name (str): The name of a model attribute that a user inputs or can be
            calculated.

    Returns:
        set[str]: Set of model attribute names that :py:attr:`name` relies on.
    """
    return nx.descendants(parameter_graph, name)
