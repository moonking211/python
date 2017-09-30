import requests
import traceback
import StringIO
import csv
import urllib
import json
import collections
from restapi.models.Ad import Ad
from restapi.models.A9Cookie import A9Cookie
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from optparse import make_option
from datetime import datetime, timedelta
from restapi.email import send_a9_scraper_error_email


class Command(BaseCommand):
    help = 'A9 Scraper'

    option_list = BaseCommand.option_list + (
                        make_option('--days', action='store',
                            dest='days',
                            default='30',
                            type='int',
                            help='Day Span'),
                        make_option('--v', action='store_true',
                            dest='verbose',
                            default=False,
                            help='Verbose'),
                        )

    def handle(self, *args, **options):
        settings.SYSTEM_USER = True
        start_time = datetime.utcnow()

        try:
            days = 30
            if 'days' in options:
                days = options['days']

            start_date = datetime.now() - timedelta(days=days)
            start_date = start_date.strftime('%m/%d/%Y')
            end_date = datetime.today().strftime('%m/%d/%Y')

            a9_cookie = A9Cookie.objects.last()
            if not a9_cookie:
                send_a9_scraper_error_email({'msg': 'A9 Scraper is required!', 'detail': ''})

            _cookies = {}
            f = StringIO.StringIO(a9_cookie.cookie_text)
            reader = csv.reader(f, delimiter='\t')
            allowed = ['s_vn', 'aws-x-main', 'x-main', 'session-id', 's_dslv', 'at-main', 'regStatus', 'aws-target-visitor-id', 'aws-at-main', 'session-id-time', 'ubid-main', '__utmz', 'aws-ubid-main', '__utmv', 'aws-userInfo', 'aws-target-data', '__utma', '_dtbportal', 'aws-target-static-id', 'session-token', 'x-wl-uid', 's_fid', 'sess-at-main']
            for row in reader:
                if not row[0] or row[0].startswith('#') or len(row)<7:
                    continue
                _key = row[5]
                _val = row[6].replace('&quot;', '"')
                if _key in allowed:
                    _cookies[_key] = _val

            _headers = {
                'Accept-Encoding': 'gzip, deflate, sdch, br',
                'Accept-Language': 'en-US,en;q=0.8',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Referer': 'https://ams.amazon.com/buyer/creatives',
                'Connection': 'keep-alive'
            }
            query = collections.OrderedDict()
            query['authenticity_token'] = a9_cookie.authenticity_token
            query['start_date'] = start_date
            query['end_date'] = end_date

            url = "https://ams.amazon.com/buyer/creatives/report-data.csv?utf8=%E2%9C%93&" + urllib.urlencode(query) + "&sSearch="
            self._log("====================> Fetching A9 Status ====================")
            self._log("URL: %s" % url)
            res = requests.get(url, cookies=_cookies, headers=_headers)

            if res.status_code == 200:
                if 'Amazon.com Sign In' in res.text and '<title>' in res.text and '</title>' in res.text:
                    if options['verbose']:
                        print 'Invalid response!'
                    send_a9_scraper_error_email({'msg': 'Invalid Response!', 'detail': res.text})

                else:
                    rows = [r.encode('utf8') for r in res.text.split('\n') if (r and '#' not in r)]
                    field_names = rows.pop(0)
                    field_names = [f.lower().replace(' ', '_') for f in field_names.split(',')]
                    _list = csv.DictReader(rows, fieldnames=field_names)
                    data = {}
                    for l in _list:
                        ad_id = l['creative_id']
                        status = l['status']
                        if options['verbose']:
                            print ad_id, status
                        data[ad_id] = status
                        ad = None
                        try:
                            ad = Ad.objects_raw.get(ad_id=ad_id)
                        except:
                            pass
                        if ad:
                            ad.a9_status = status
                            ad.save_raw()

                    self._log("A9 Updates: %s" % json.dumps(data))
                    self.update_job_status()
                    end_time = datetime.utcnow()
                    self._log('Script Duration: {}'.format(end_time - start_time))

            else:
                send_a9_scraper_error_email({'msg': 'status_code is not 200', 'detail': res.text})

        except Exception as e:
            if options['verbose']:
                print 'Error: %s' % str(e)
            send_a9_scraper_error_email({'msg': str(e), 'detail': traceback.format_exc()})

    def update_job_status(self):
        sql = "REPLACE INTO job_status SET job_name='a9_scraper', job_type='rtb', last_finished=NOW(), threshold=1440"
        cursor = connection.cursor()
        try:
            cursor.execute(sql)
        except:
            return False
        finally:
            cursor.close()
            return True

    def _log(self, s):
        print datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(s)
