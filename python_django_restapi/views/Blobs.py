import hashlib
import mimetypes
import os
import re
from PIL import Image
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework import generics
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.status import HTTP_202_ACCEPTED
from rest_framework.status import HTTP_409_CONFLICT
from restapi.models.choices import AD_TYPE_DISPLAY
from restapi.models.choices import AD_TYPE_VIDEO
from restapi.models.choices import AD_TYPE_NATIVE


class Blobs(generics.GenericAPIView):
    parser_classes = (MultiPartParser, )
    # permission_classes = (IsAuthenticated, )

    def __init__(self, *args, **kwargs):
        super(Blobs, self).__init__(*args, **kwargs)

    def get_hash(self, data_file):
        hash_obj = hashlib.md5()
        for chunk in data_file.chunks(chunk_size=128 * hash_obj.block_size):
            hash_obj.update(chunk)
        return hash_obj.hexdigest()

    @staticmethod
    def _move_data(new_path, old_path):
        if not default_storage.exists(new_path):
            with default_storage.open(old_path, 'r') as data_file:
                data_file = data_file.read()
                default_storage.save(new_path, ContentFile(data_file))

    # pylint: disable=redefined-builtin,unused-argument
    def post(self, request, format=None):
        """
        POST /blobs

        :param request:
        :param format:
        :return:
        """
        ad_type = request.QUERY_PARAMS.get('adType', '0')
        try:
            ad_type = int(ad_type)
        except:
            pass

        input_file = request.FILES['file']

        # validation warnings
        warnings = []
        match = re.search(r'\.(jpg|png|gif)$', input_file.name, re.I)
        if match:
            sizes_static = None
            sizes_animated = None
            if ad_type == AD_TYPE_DISPLAY:
                sizes_static = {'1024x768': 200000, '768x1024': 200000,
                                '750x560':  100000, '560x750':  100000,
                                '480x320':   50000, '320x480':   50000,
                                '300x250':   40000,
                                '728x90':    40000,
                                '375x50':    50000,
                                '320x50':    30000}
                sizes_animated = {'1024x768': 500000, '768x1024': 500000,
                                  '750x560':  500000, '560x750':  500000,
                                  '480x320':  200000, '320x480':  200000,
                                  '300x250':  200000,
                                  '728x90':   200000,
                                  '375x50':    50000,
                                  '320x50':    50000}
            elif ad_type == AD_TYPE_VIDEO:
                sizes_static = {'320x480': 100000, '480x320': 100000,
                                '1024x768':200000,'768x1024': 200000}
                sizes_animated = {'320x480': 100000, '480x320': 100000,
                                  '1024x768':200000,'768x1024': 200000}
            elif ad_type == AD_TYPE_NATIVE:
                sizes_static = {'1200x627': 200000,
                                '80x80':    20000}
                sizes_animated = {'1200x627': 200000,
                                  '80x80':    20000}

            image = Image.open(input_file)
            try:
                image.seek(1)
            except EOFError:
                sizes = sizes_static
            else:
                sizes = sizes_animated

            if sizes:
                width, height = image.size
                px_size = "{}x{}".format(width, height)
                max_size = sizes[px_size] if px_size in sizes else 145000
                if input_file.size > max_size:
                    warnings.append('Actual {} KB, Recommended up to {} KB.'.format(int(input_file.size/1000), int(max_size/1000)))

        path = "{}/{}".format(request.QUERY_PARAMS['outputPrefix'], input_file.name.replace(' ', '_').replace('+', '_'))
        if not default_storage.exists(path):
            default_storage.save(path, input_file)
            status = HTTP_201_CREATED
        else:
            with default_storage.open(path, 'r') as data_file:
                amazon_etag = data_file.key.etag
            local_etag = self.get_hash(input_file)

            if local_etag != amazon_etag.strip('"'):
                status = HTTP_409_CONFLICT
                warnings.append('Another file with the same name({}) already exists'.format(input_file.name))
            else:
                status = HTTP_202_ACCEPTED

        relative_path = path[1:] if path[0] == '/' else path

        uri = ''
        if settings.MNG_CDN is None:
            uri = "https://{}.s3.amazonaws.com/{}".format(settings.AWS_STORAGE_BUCKET_NAME, path)

            if settings.MNG_NOCDN_PROTO:
                uri = re.sub(r'^(.*?\w+:\/\/|)', '%s://' % settings.MNG_NOCDN_PROTO, uri)
        else:
            ending = settings.MNG_CDN[len(settings.MNG_CDN) - 1]
            cdn_base = settings.MNG_CDN[0:len(settings.MNG_CDN) - 1] if ending == '/' else settings.MNG_CDN
            uri = '{0}/{1}'.format(cdn_base, relative_path)

        blob = {
            'path': relative_path,
            'uri': uri,
            'mime': mimetypes.guess_type(uri)[0] or 'application/octet-stream'
        }
        if warnings:
            blob['warnings'] = warnings
        return Response(blob, status=status)
