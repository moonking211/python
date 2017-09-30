import csv
import json
import requests
import StringIO
from django.http import HttpResponse
from django.http import StreamingHttpResponse
from restapi.views.Reports import Reports


class NoBidReports(Reports):
    def get(self, request):
        headers = {'Authorization': 'token token="%s"' % self.trading_desk_key}
        api_response = requests.get(self.get_url(), headers=headers, verify=False, stream=True)

        status_code = int(api_response.status_code)
        content_type = api_response.headers.get('content-type', 'text/csv')

        if status_code != 200:
            data = json.dumps({'info': api_response.text})
            return HttpResponse(data, status=status_code, content_type=content_type)

        if content_type != 'text/csv':
            return HttpResponse(api_response.text, status=status_code, content_type=content_type)

        this = self

        def stream_response_generator():
            data = []
            headers = []
            for line in api_response.iter_lines():
                data = csv.reader([line]).next()
                output = StringIO.StringIO()
                writer = csv.writer(output)
                row = this.select_data(headers, data)
                writer.writerow(row)
                yield output.getvalue()

        response = StreamingHttpResponse(stream_response_generator(), status=status_code, content_type=content_type)
        response['Content-Disposition'] = 'inline; filename="report.csv'

        return response
