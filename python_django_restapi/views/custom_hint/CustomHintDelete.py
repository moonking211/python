from restapi.models.CustomHint import CustomHint
from restapi.models.CustomHint import CustomHintIds
from restapi.views.BasePlasementDelete import BasePlasementDelete


class CustomHintDelete(BasePlasementDelete):
    model = CustomHint
    modelIds = CustomHintIds
