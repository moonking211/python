from django.utils.timezone import now
from decimal import Decimal
from datetime import datetime
import json

from restapi.testspecs.CreateTestClient import CreateTestClient
from restapi.models.choices import STATUS_ENABLED, STATUS_PAUSED, CURRENCY_USD, AD_SIZE_CHOICES
from restapi.models.Advertiser import Advertiser
from restapi.models.Campaign import Campaign
from restapi.models.AdGroup import AdGroup
from restapi.models.Agency import Agency
from restapi.models.Ad import Ad
from restapi.models.Event import Event
from restapi.models.Revmap import Revmap
from restapi.models.Currency import Currency
from restapi.models.TradingDesk import TradingDesk, MANAGE_TRADING_DESK_ID
from restapi.models.TrackingProvider import TrackingProvider


class CreateTestData(CreateTestClient):
    def create_trading_desk(self, trading_desk_name='trading desk', currency=CURRENCY_USD,
                            contact='contact info', account_manager=MANAGE_TRADING_DESK_ID, status=STATUS_ENABLED):
        trading_desk = TradingDesk(trading_desk=trading_desk_name, currency=currency,
                                   contact=contact, account_manager=account_manager, status=status)

        trading_desk.save()
        self.fill_in_currency()

        return trading_desk

    def create_agency(self, agency_name='agency', status=STATUS_ENABLED, currency=CURRENCY_USD,
                      contact='contact info', account_manager=MANAGE_TRADING_DESK_ID):
        agency = Agency(trading_desk_id=self.user.profile.trading_desk.first(), agency=agency_name,
                        status=status, currency=currency, contact=contact, account_manager=account_manager)
        agency.save()
        self.fill_in_currency()

        return agency

    def create_advertiser(self,
                          agency=None,
                          advertiser_name='advertiser 1',
                          sampling_rate='0',
                          throttling_rate='0',
                          flight_start_date='2000-01-01',
                          currency='CAD',
                          contact='contact_person',
                          encryption_key='encryption_key',
                          encryption_iv='encryption_iv',
                          encryption_suffix='encryption_suffix'):
        if agency is None:
            agency = self.create_agency()

        advertiser = Advertiser(agency_id=agency,
                                advertiser=advertiser_name,
                                sampling_rate=sampling_rate,
                                throttling_rate=throttling_rate,
                                flight_start_date=flight_start_date,
                                currency=currency,
                                contact=contact,
                                encryption_key=encryption_key,
                                encryption_iv=encryption_iv,
                                encryption_suffix=encryption_suffix)
        advertiser.save()
        return advertiser

    def fill_in_currency(self):
        Currency(currency_name='USD', currency_code='USD').save()
        Currency(currency_name='CAD', currency_code='CAD').save()

    def create_campaign(self, advertiser_id=None, campaign_name='campaign 1',
                        flight_start_date=None, flight_end_date=None, redirect_url='https://google.com', genre=1):
        if advertiser_id is None:
            advertiser_id = self.create_advertiser()

        if flight_start_date is None:
            flight_start_date = datetime.now()

        if flight_end_date is None:
            flight_end_date = datetime.now()

        campaign = Campaign(advertiser_id=advertiser_id, campaign=campaign_name, redirect_url=redirect_url,
                            flight_start_date=flight_start_date, flight_end_date=flight_end_date, genre=genre,
                            targeting='{"country":["USA"], "os":"Android"}')
        campaign.save()

        return campaign

    def create_ad_group(self, campaign_id=None, ad_group_name='ad group',
                        frequency_map={"*": "1/28800", "0x0": "3/86400", "320x50": "1/7200", "728x90": "1/7200"},
                        frequency_interval=1, max_frequency=2, status=STATUS_PAUSED, inflator_text="* 1.00",
                        flight_start_date=None, flight_end_date=None, distribution_web=True):
        if campaign_id is None:
            campaign_id = self.create_campaign()

        if flight_start_date is None:
            flight_start_date = datetime.now()

        if flight_end_date is None:
            flight_end_date = datetime.now()

        ad_group = AdGroup(campaign_id=campaign_id, ad_group=ad_group_name, frequency_map=frequency_map,
                           frequency_interval=frequency_interval, max_frequency=max_frequency, status=status,
                           flight_start_date=flight_start_date, flight_end_date=flight_end_date,
                           inflator_text=inflator_text, distribution_web=distribution_web)
        ad_group.save()

        return ad_group

    def create_ad(self, campaign_id=None, ad_group_id=None, ad_name='ad', creative_id=0, ad_type=1, bid=0,
                  html='<a href="{CLICK_URL}"><img src="https://cdn.manage.com/71/iMob_300x250_2Girls.jpg" width="300" height="250"></a>',
                  i_url='http://ya.ru/', size=AD_SIZE_CHOICES[0][0], status=STATUS_PAUSED, inflator_text="* 1.00"):
        if ad_group_id is None:
            ad_group_id = self.create_ad_group()

        if campaign_id is None:
            campaign_id = ad_group_id.campaign_id

        ad = Ad(campaign_id=campaign_id, ad_group_id=ad_group_id, ad=ad_name, creative_id=creative_id,
                ad_type=ad_type, bid=bid, html=html, i_url=i_url, size=size, status=status, inflator_text=inflator_text)
        ad.save()

        return ad

    def create_revmap(self, ad_group_id=None, ad_group_name='ad_group', campaign_id=None, campaign_name='campaign',
                      opt_type='install', opt_value=Decimal('12345.6789'), rev_type='install',
                      rev_value=Decimal('12345.6789'), target_type='install', target_value=Decimal('12345.6789'),
                      last_update=None):

        if last_update is None:
            last_update = now()

        if ad_group_id is None:
            ad_group_id = self.create_ad_group()

        if campaign_id is None:
            campaign_id = self.create_campaign()

        revmap = Revmap(ad_group_id=ad_group_id, ad_group=ad_group_name, campaign_id=campaign_id,
                        campaign=campaign_name, opt_type=opt_type, opt_value=opt_value, rev_type=rev_type,
                        rev_value=rev_value, target_type=target_type, target_value=target_value,
                        last_update=last_update)
        revmap.save()

        return revmap

    def create_event(self, event_name='event 1',
                     max_frequency=123,
                     frequency_interval=1,
                     base_event_id=0,
                     campaign_id=None):

        if campaign_id is None:
            campaign_id = self.create_campaign()

        event = Event(event=event_name,
                      max_frequency=max_frequency,
                      frequency_interval=frequency_interval,
                      base_event_id=base_event_id,
                      campaign_id=campaign_id)
        event.save()
        return event

    def create_tracking_provider(self):
        tracking_provider = TrackingProvider(tracking_provider_id=1, tracking_provider='test_provider')
        tracking_provider.save()
        return tracking_provider
