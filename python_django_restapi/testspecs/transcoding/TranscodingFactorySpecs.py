from mock import Mock
from mng.test import spec
from restapi.transcoding import TranscodingFactory


class TranscodingFactorySpecs(spec(TranscodingFactory)):
    #pylint: disable=no-self-use,invalid-name
    def test__create_connection__takes_args_from_settings_and_creates_an_instance_of_ElasticTranscoderConnection(self):
        # arrange
        region1 = Mock()
        region1.name = 'region1'
        connection = Mock()
        settings = {
            'REGION': 'region1',
            'AWS_ACCESS_KEY': 'ak1',
            'AWS_SECRET_KEY': 'sk1'
        }
        get_regions = lambda: [region1]
        ctor = Mock(return_value=connection)
        subject = TranscodingFactory(get_regions=get_regions, connection_cls=ctor, transcoding_settings=settings)

        # act
        return_value = subject.create_connection()

        # assert
        ctor.assert_called_with(region=region1, aws_access_key_id='ak1', aws_secret_access_key='sk1')
        assert connection is return_value
