from mock import Mock
from mng.test import spec
from restapi.views.Transcoding import Transcoding


class TranscodingSpecs(spec(Transcoding)):
    subject = None
    request = None
    etc = None

    def before_each(self):
        self.etc = Mock()
        create_job_result1 = {
            'Job': {
                'Id': 'job1',
                'Status': 'Submitted'
            }
        }
        self.etc.create_job = Mock(return_value=create_job_result1)
        transcoding_service = Mock()
        transcoding_service.create_connection = Mock(return_value=self.etc)
        transcoding_settings = {
            'BUCKET': '1',
            'FILE_PATTERN': 'https://{bucket}.s3.amazonaws.com/{key}',
            'PIPELINE_ID': 'pipeline1',
            'PRESET_ID_MPEG4_270P': 'preset_mpeg4',
            'PRESET_ID_WEBM_270P': 'preset_webm',
        }
        transcoding_formats = {
            '480x270': ('preset_mpeg4', 'preset_webm'),
        }
        self.subject = Transcoding(
            transcoding_factory_cls=Mock(return_value=transcoding_service),
            transcoding_settings=transcoding_settings,
            transcoding_formats=transcoding_formats,
            rnd=lambda: 123123123
        )
        self.request = Mock()
        self.request.DATA = {
            'path': 'dir/file.mpg',
            'outputPrefix': 'videos/'
        }

    def test__post__schedules_video_transcoding_to_mpeg4_and_mpeg4(self):
        # act
        self.subject.post(self.request)

        # assert
        self.etc.create_job.assert_called_with(
            pipeline_id='pipeline1',
            input_name={'Key': 'dir/file.mpg'},
            outputs=[
                {
                    'Width': '480',
                    'ThumbnailPattern': 'file_480x270_123123123000_mp4_thumb_{count}',
                    'PresetId': 'preset_mpeg4',
                    'Key': 'file_480x270_123123123000.mp4',
                    'Height': '270'
                },
                {
                    'Width': '480',
                    'ThumbnailPattern': 'file_480x270_123123123000_webm_thumb_{count}',
                    'PresetId': 'preset_webm',
                    'Key': 'file_480x270_123123123000.webm',
                    'Height': '270'
                }
            ],
            output_key_prefix='videos/'
        )

    def test__post__returns_job_details_when_successfully_scheduled(self):
        # act
        response = self.subject.post(self.request)
        result = response.data

        # assert
        assert response.status_code == 201
        assert result['id'] == 'job1'
        assert result['status'] == 'Submitted'
        assert len(result['outputs']) == 2
        assert result['outputs'][0]['mime'] == 'video/mpeg4'
        assert result['outputs'][0]['path'] == 'https://1.s3.amazonaws.com/videos/file_480x270_123123123000.mp4'
        #pylint: disable=line-too-long
        assert result['outputs'][0]['thumbnail'] == 'https://1.s3.amazonaws.com/videos/file_480x270_123123123000_mp4_thumb_00001.jpg'
        assert result['outputs'][1]['mime'] == 'video/webm'
        assert result['outputs'][1]['path'] == 'https://1.s3.amazonaws.com/videos/file_480x270_123123123000.webm'
        #pylint: disable=line-too-long
        assert result['outputs'][1]['thumbnail'] == 'https://1.s3.amazonaws.com/videos/file_480x270_123123123000_webm_thumb_00001.jpg'

    def test__get__returns_job_details(self):
        # arrange
        self.etc.read_job = Mock(return_value={'Job': {'Status': 'Complete'}})

        # act
        response = self.subject.get(Mock(), 'job123')
        result = response.data

        # assert
        self.etc.read_job.assert_called_with('job123')
        assert response.status_code == 200
        assert result['status'] == 'Complete'

