import os
import time
from django.conf import settings
from rest_framework import views
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED
from restapi.transcoding import TranscodingFactory


class Transcoding(views.APIView):
    # permission_classes = (IsAuthenticated, )

    def __init__(self, *args, **kwargs):
        self.transcoding_factory_cls = kwargs.pop('transcoding_factory_cls', TranscodingFactory)
        self.transcoding_settings = kwargs.pop('transcoding_settings', settings.MNG_TRANSCODING_SETTINGS)
        self.transcoding_formats = kwargs.pop('transcoding_formats', settings.TRANSCODING_FORMATS)
        self.rnd = kwargs.pop('rnd', time.time)
        super(Transcoding, self).__init__(*args, **kwargs)

    # todo VN remove this workaround
    # pylint: disable=unused-argument
    def generate_url(self, conn, path):
        pattern = self.transcoding_settings['FILE_PATTERN']
        return pattern.format(bucket=self.transcoding_settings['BUCKET'], key=path)

    # pylint: disable=unused-argument
    def post(self, request, *args, **kwargs):
        transcoding_settings = self.transcoding_settings
        transcoding_formats = self.transcoding_formats
        data = request.DATA
        path = data['path']  # 'uploads/rnd/random.mpg'
        output_prefix = data['outputPrefix'].strip('/').strip('\\').replace('\\', '/')  # '12435'
        filename = os.path.basename(path)
        # pylint: disable=unused-variable
        name, ext = os.path.splitext(filename)
        width, height = data.get('width', None), data.get('height', None)
        if width and height:
            dst_filename = name + '_' + width + 'x' + height + '_' + str(long(round(self.rnd() * 1000)))
        else:
            dst_filename = name + '_480x270_' + str(long(round(self.rnd() * 1000)))
            width = '480'
            height = '270'

        preset_key = width + 'x' + height
        mp4_presetId, webm_preseId = transcoding_formats[preset_key]
        output_key_prefix = output_prefix + '/'

        job_request = {
            'pipeline_id': transcoding_settings['PIPELINE_ID'],
            'input_name': {
                'Key': path
            },
            'output_key_prefix': output_key_prefix,
            'outputs': [
                {
                    'Key': dst_filename + '.mp4',
                    'Width': width,
                    'Height': height,
                    'PresetId': mp4_presetId,
                    'ThumbnailPattern': dst_filename + '_mp4_thumb_{count}'
                },
                {
                    'Key': dst_filename + '.webm',
                    'Width': width,
                    'Height': height,
                    'PresetId': webm_preseId,
                    'ThumbnailPattern': dst_filename + '_webm_thumb_{count}'
                }
            ]
        }
        etc = self.transcoding_factory_cls().create_connection()
        job_response = etc.create_job(**job_request)
        job_id = job_response['Job']['Id']
        job = {
            'id': job_id,
            'status': job_response['Job']['Status'],
            'job': job_response['Job'],
            'outputs': [
                {
                    'mime': 'video/mpeg4',
                    'path': self.generate_url(etc, output_key_prefix + dst_filename + '.mp4'),
                    'thumbnail': self.generate_url(etc, output_key_prefix + dst_filename + '_mp4_thumb_00001.jpg')
                },
                {
                    'mime': 'video/webm',
                    'path': self.generate_url(etc, output_key_prefix + dst_filename + '.webm'),
                    'thumbnail': self.generate_url(etc, output_key_prefix + dst_filename + '_webm_thumb_00001.jpg')
                }
            ]
        }
        return Response(job, status=HTTP_201_CREATED)

    # pylint: disable=unused-argument
    def get(self, request, job_id, *args, **kwargs):
        etc = self.transcoding_factory_cls().create_connection()
        job_response = etc.read_job(job_id)
        job = {
            'id': job_id,
            'status': job_response['Job']['Status'],
            'job': job_response['Job']
        }
        return Response(job, status=HTTP_200_OK)
