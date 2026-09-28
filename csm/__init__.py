from csm.models import CSMBase, Land2015NLR, Land2020NLR, Land2021NLR, available_models
from csm.models.utils import make_name_variations


__version__ = "0.0.1"


def get_model(name: str | int) -> type[CSMBase]:
    """Retrieves the desired model class based on the model name or alias :py:attr:`name`.

    Args:
        name (str | int): A model name or valid alias for a model. Aliases are as follows:

            - :py:class:`CSMBase`: "base", "CSMBase"
            - :py:class:`Land2015NLR`: "2015", 2015, "nlr2015", "land2015", "Land2015NLR", "NLR 2015"
            - :py:class:`Land2020NLR`: "2020", 2020, "nlr2020", "land2020", "Land2020NLR", "NLR 2020"
            - :py:class:`Land2021NLR`: "2021", 2021, "nlr2021", "land2021", "Land2021NLR", "NLR 2021"

    Raises:
        NotImplementedError: Raised if :py:attr:`name` is an invalid model name or alias.

    Returns:
        Type[CSMBase]: The ``CSMBase`` model or one of its subclasses.
    """
    if name in ("base", "CSMBase"):
        return CSMBase
    if name in make_name_variations(source="nlr", basis="land", year=2015):
        return Land2015NLR
    if name in make_name_variations(source="nlr", basis="land", year=2020):
        return Land2020NLR
    if name in make_name_variations(source="nlr", basis="land", year=2021):
        return Land2021NLR
    raise NotImplementedError(f"'{name}' is invalid, use one of: {available_models}.")
