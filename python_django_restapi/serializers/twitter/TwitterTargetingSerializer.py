from rest_framework import serializers
from restapi.models.twitter.TwitterTargetingModels import *
from restapi.models.twitter.TwitterLineItem import TwitterLineItem
from restapi.models.twitter.TwitterTailoredAudience import TwitterTailoredAudience
from restapi.serializers.fields.PKRelatedField import PKRelatedField
from restapi.models.twitter.TwitterTVTargeting import *
from restapi.models.twitter.TwitterBehaviorTargeting import *
from restapi.views.twitter.helper import human_format


class TwitterTargetingDetailSerializer(serializers.ModelSerializer):
    extra = serializers.SerializerMethodField()
    tw_line_item_id = PKRelatedField(queryset=TwitterLineItem.objects_raw.all())
    class Meta:
        model = TwitterTargeting
        fields = ('tw_criteria_id',
                  'name',
                  'tw_line_item_id',
                  'tw_targeting_type',
                  'tw_targeting_id',
                  'extra',
                  'targeting_value',
                  'targeting_params')

    def get_extra(self, obj):
        if obj.tw_targeting_type == 4:
            return TwitterDevice.objects_raw.get(pk=obj.tw_targeting_id).platform
        #if obj.tw_targeting_type == 14:
        #    return TwitterAppCategory.objects_raw.get(pk=obj.tw_targeting_id).platform
        if obj.tw_targeting_type == 15:
            return TwitterCarrier.objects_raw.get(pk=obj.tw_targeting_id).country_code
        if obj.tw_targeting_type == 16:
            return TwitterOsVersion.objects_raw.get(pk=obj.tw_targeting_id).platform
        if obj.tw_targeting_type == 17:
            return TwitterUserInterest.objects_raw.get(pk=obj.tw_targeting_id).category
        if obj.tw_targeting_type == 18:
            return TwitterTailoredAudience.objects_raw.get(pk=obj.tw_targeting_id).name
        if obj.tw_targeting_type == 22:
            b = TwitterBehavior.objects_raw.get(pk=obj.tw_targeting_id)
            _path = []
            _path.append(b.tw_behavior_taxonomy.name)
            if b.tw_behavior_taxonomy.parent:
                _path.append(b.tw_behavior_taxonomy.parent.name)
            _path.reverse()

            return dict(name=b.name, path=': '.join(_path))

        return ''

class TwitterTargetingSerializer(serializers.ModelSerializer):
    tw_line_item_id = PKRelatedField(queryset=TwitterLineItem.objects_raw.all())
    name = serializers.CharField(required=True, allow_blank=False)
    tw_targeting_type = serializers.CharField(required=True, allow_blank=False)
    tw_targeting_id = serializers.CharField(required=False, allow_blank=True)
    targeting_value = serializers.CharField(required=False, allow_blank=True)
    targeting_params = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = TwitterTargeting
        fields = ('tw_criteria_id',
                  'name',
                  'tw_line_item_id',
                  'tw_targeting_type',
                  'tw_targeting_id',
                  'targeting_value',
                  'targeting_params')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=TwitterTargeting.objects_raw.all(),
                fields=('tw_line_item_id', 'name')
            )
        ]

class TwitterAppCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TwitterAppCategory


class TwitterCarrierSerializer(serializers.ModelSerializer):
    class Meta:
        model = TwitterCarrier


class TwitterLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TwitterLocation


class TwitterOsVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TwitterOsVersion


class TwitterUserInterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TwitterUserInterest


class TwitterDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TwitterDevice


class TwitterTVMarketSerializer(serializers.ModelSerializer):
    location_id = serializers.SerializerMethodField()

    class Meta:
        model = TwitterTVMarket
        fields = ('tw_tv_market_id', 'name', 'country_code', 'locale', 'location_id')

    def get_location_id(self, obj):
        loc = TwitterLocation.objects_raw.filter(location_name=obj.name).first()
        if loc:
            return loc.tw_targeting_id
        return ''

class TwitterTVGenreSerializer(serializers.ModelSerializer):
    id_str = serializers.SerializerMethodField()

    class Meta:
        model = TwitterTVGenre
        fields = ('tw_targeting_id',
                  'id_str',
                  'name')
    def get_id_str(self, obj):
        return 'i%s:%s' % (obj.tw_targeting_id, obj.name)

class TwitterTVChannelSerializer(serializers.ModelSerializer):
    id_str = serializers.SerializerMethodField()

    class Meta:
        model = TwitterTVChannel
        fields = ('tw_targeting_id',
                  'id_str',
                  'name')

    def get_id_str(self, obj):
        return 'i%s:%s' % (obj.tw_targeting_id, obj.name)


class TwitterBehaviorTaxonomySerializer(serializers.ModelSerializer):
    class Meta:
        model = TwitterBehaviorTaxonomy
        fields = ('tw_behavior_taxonomy_id', 'name', 'US', 'GB', 'parent')


class TwitterBehaviorSerializer(serializers.ModelSerializer):
    taxonomy_path = serializers.SerializerMethodField()
    audience_size_str = serializers.SerializerMethodField()

    class Meta:
        model = TwitterBehavior
        fields = ('tw_targeting_id', 'name', 'tw_behavior_taxonomy', 'country_code', 'taxonomy_path',
                  'audience_size_str')

    def get_taxonomy_path(self, obj):
        _path = []
        _path.append(obj.tw_behavior_taxonomy.name)
        if obj.tw_behavior_taxonomy.parent:
            _path.append(obj.tw_behavior_taxonomy.parent.name)
        _path.reverse()
        return ': '.join(_path)

    def get_audience_size_str(self, obj):
        return human_format(obj.audience_size)