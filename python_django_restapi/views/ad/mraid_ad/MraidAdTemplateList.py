from restapi.models.MraidAdTemplate import MraidAdTemplate
from restapi.serializers.MraidAdTemplateSerializer import MraidAdTemplateSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate
from itertools import groupby


def transform_templates(response, templates):
    result_array = []
    for key, group in groupby(templates, lambda x: x['template_name']):
        grouper = [
            dict({
                'js_tag_version': item['js_tag_version'],
                'banner_tag_version': item['banner_tag_version'],
                'template': item['template']})
            for item in group]
        result_array.append({'template_name': key, 'template_params': grouper})
    response.data['results'] = result_array


class MraidAdTemplateList(BaseListCreate):
    serializer_class = MraidAdTemplateSerializer

    @property
    def queryset(self):
        return MraidAdTemplate.objects.all()

    def finalize_response(self, request, response, *args, **kwargs):
        response = super(MraidAdTemplateList, self).finalize_response(request, response, *args, **kwargs)
        try:
            results = response.data['results']
            if not results:
                return response
            transform_templates(response=response, templates=results)
        except KeyError:
            pass
        except TypeError:
            results = response.data
            if not results:
                return response
            transform_templates(response=response, templates=results)

        return response
