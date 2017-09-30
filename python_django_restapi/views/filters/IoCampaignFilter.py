import django_filters

class IoCampaignFilter(django_filters.FilterSet):
    campaigns = django_filters.CharFilter(
        campaign_id='campaigns__campaign_id',
    )

class Meta:
    model = IoCampaignFilter
    fields = ('campaign_id',)