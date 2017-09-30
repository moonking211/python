from boto.elastictranscoder.layer1 import ElasticTranscoderConnection
from boto.elastictranscoder import regions
from django.conf import settings


class TranscodingFactory(object):
    def __init__(
            self,
            get_regions=regions,
            connection_cls=ElasticTranscoderConnection,
            transcoding_settings=settings.MNG_TRANSCODING_SETTINGS
    ):
        self.connection_cls = connection_cls
        self.get_regions = get_regions
        self.transcoding_settings = transcoding_settings

    def create_connection(self):
        """
        :rtype: boto.elastictranscoder.layer1.ElasticTranscoderConnection
        :return: An instance of boto.elastictranscoder.layer1.ElasticTranscoderConnection
        """
        region_name = self.transcoding_settings['REGION']
        for region in self.get_regions():
            if region.name == region_name:
                connection = self.connection_cls(
                    region=region,
                    aws_access_key_id=self.transcoding_settings['AWS_ACCESS_KEY'],
                    aws_secret_access_key=self.transcoding_settings['AWS_SECRET_KEY']
                )
                return connection
        return None
