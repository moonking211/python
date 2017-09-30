import sys
import mimetypes
import types
from optparse import make_option
from boto.s3.connection import S3Connection, ProtocolIndependentOrdinaryCallingFormat
from boto.cloudfront import CloudFrontConnection
from django.conf import settings
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Fixes S3 Content Type'
    option_list = BaseCommand.option_list  + (
                        make_option('--bucket_name', action='store',
                            dest='bucket_name',
                            default='',
                            help='AWS Bucket'),
                        )

    def handle(self, *args, **options):

        bucket_name = settings.MNG_TRANSCODING_SETTINGS.get('BUCKET')
        if 'bucket' in options:
            bucket_name = options['bucket_name']

        aws_key    = settings.MNG_TRANSCODING_SETTINGS.get('AWS_ACCESS_KEY')
        aws_secret = settings.MNG_TRANSCODING_SETTINGS.get('AWS_SECRET_KEY')

        s3_conn = S3Connection(aws_key, aws_secret, calling_format=ProtocolIndependentOrdinaryCallingFormat())

        s3_bucket = s3_conn.get_bucket(bucket_name)
        keys = s3_bucket.list()

        for key in keys:
            if type(key) == types.StringType:
                key_name = key
                key = s3_bucket.get_key(key)
                if not key:
                    print 'Key not found %s' % key_name
                    continue

            key = s3_bucket.get_key(key.name)
            if key and 'name' in key:
                file_content_type_check = mimetypes.guess_type(key.name)[0]
                print key.name
                if file_content_type_check and key.content_type != file_content_type_check:
                    metadata = key.metadata
                    metadata['Content-Type'] = file_content_type_check
                    print "==> MISMATCH: " + str(key) + ", " + str(key.content_type) + " => " + str(file_content_type_check)
                    key.copy(bucket_name, key, metadata=metadata, preserve_acl=True)



