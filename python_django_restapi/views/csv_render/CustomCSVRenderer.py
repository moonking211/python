import csv
from pytz import timezone
from django.conf import settings
from dateutil.parser import parse
from datetime import date, datetime, time

from rest_framework_csv import renderers
from collections import OrderedDict
from six import StringIO, text_type


class CustomCSVRenderer(renderers.CSVRenderer):
    results_field = 'results'
    media_type = 'text/csv'
    format = 'csv'
    level_sep = '.'
    headers = None
    labels = None

    def render(self, data, media_type=None, renderer_context={}, writer_opts=None):
        """
        Renders serialized *data* into CSV. For a dictionary:
        """
        if data is None:
            return ''

        # {'<field>':'<label>'}
        self.labels = renderer_context.get('labels', self.labels)
        self.headers = renderer_context.get('headers', self.headers)

        if not isinstance(data, list):
            data = [data]

        if writer_opts is None:
            writer_opts = {}

        table = self.tablize(data)
        csv_buffer = StringIO()
        csv_writer = csv.writer(csv_buffer, dialect=csv.excel, **writer_opts)
        for row in table:
            # Assume that strings should be encoded as UTF-8
            csv_writer.writerow([
                elem.encode('utf-8') if isinstance(elem, text_type) else elem
                for elem in row
            ])

        return csv_buffer.getvalue()

    def flatten_dict(self, d):
        flat_dict = OrderedDict()
        for key, item in d.items():
            key = text_type(key)
            flat_item = self.flatten_item(item)
            nested_item = self.nest_flat_item(flat_item, key)
            flat_dict.update(nested_item)
        return flat_dict

    def tablize(self, data):
        """
        Convert a list of data into a table.
        """
        if data:

            # First, flatten the data (i.e., convert it to a list of
            # dictionaries that are each exactly one level deep).  The key for
            # each item designates the name of the column that the item will
            # fall into.
            data = self.flatten_data(data)
            data.header = data.header or self.headers

            # Get the set of all unique headers, and sort them (unless already provided).
            if not data.header:
                headers = OrderedDict()
                for item in data:
                    headers = OrderedDict((item, None) for item in item).keys()
                    # Remove M2M Reference for IO
                    headers = [item for item in headers if 'campaigns.' not in item]
                data.header = headers

            # Create a row for each dictionary, filling in columns for which the
            # item has no data with None values.
            rows = []
            for item in data:
                for key, value in item.iteritems():
                    if key == 'flight_start_date' \
                    or key == 'flight_end_date' \
                    or key == 'start_date' \
                    or key == 'end_date':
                        if value is not None and value != ''and value != '0000-00-00 00:00:00':
                            # pylint: disable=no-member
                            item[key] = self.__get_date(value)

                row = []
                for key in data.header:
                    row.append(item.get(key, None))
                rows.append(row)

            # Return your "table", with the headers as the first row.
            return [data.header] + rows

        else:
            return []

    # pylint: disable=unused-argument,no-self-use
    def __get_date(self, value):
        if isinstance(value, date):
            date_csv = value.strftime("%Y-%m-%d")
        else:

            try:
                date_csv = parse(value).astimezone(timezone(settings.TIME_ZONE))

                # if date from CH
                if date_csv.year < 1900:
                    date_csv = datetime.combine(date(1000, 01, 01), time(0, 0, 0))

                elif date_csv.year > 9000:
                    date_csv = datetime.combine(date(9999, 12, 31), time(12, 59, 59))

                else:
                    date_csv = date_csv.strftime("%Y-%m-%d %H:%M:%S")

            # if date from IO
            except ValueError:
                date_csv = value

        return date_csv
