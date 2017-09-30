# pylint: disable=too-many-lines

# 1=, 2=location, 3=platform, 4=device, 5=, 6=,
# 7=, 8=followers, 9=similar_followers, 10=broad_keyword, 11=unordered_keyword,
# 12=phrase_keyword, 13=exact_keyword, 14=app_store_category, 15=network_operator, 16=os_version, 17=user_interest
# 18=tailored_audience, 19=tv_genre, 20=tv_channel, 21=tv_shows, 22=behavior_expanded, 23=event, 24=behavior

TW_TARGETING_ID_TO_ENUM = {
    2:  'LOCATION',
    3:  'PLATFORM',
    4:  'DEVICE',
    5:  'WIFI_ONLY',
    8:  'FOLLOWERS_OF_USER',
    9:  'SIMILAR_TO_FOLLOWERS_OF_USER',
    10: 'BROAD_KEYWORD',
    11: 'UNORDERED_KEYWORD',
    12: 'PHRASE_KEYWORD',
    13: 'EXACT_KEYWORD',
    14: 'APP_STORE_CATEGORY',
    15: 'NETWORK_OPERATOR',
    16: 'PLATFORM_VERSION',
    17: 'INTEREST',
    18: 'TAILORED_AUDIENCE',
    19: 'TV_GENRE',
    20: 'TV_CHANNEL',
    21: 'TV_SHOW',
    22: 'BEHAVIOR_EXPANDED',
    23: 'EVENT',
    24: 'BEHAVIOR',
}

TW_TARGETING_ID_EXCEL_COL = {
    2:  35,
    3:  38,
    4:  40,
    5:  41,
    8:  36,
    9:  37,
    10: 48,
    11: 50,
    12: 52,
    13: 46,
    14: 66,
    15: 44,
    16: 39,
    17: 43,
    18: [54, 55, 60, 61],
    19: 70,
    20: 71,
    21: 72,
    22: 59,
    23: 74,
    24: 59,
}

# Reverse TW_TARGETING_ID_TO_ENUM
TW_TARGETING_ENUM_TO_ID = dict((v,k) for k,v in TW_TARGETING_ID_TO_ENUM.iteritems())

TW_TARGETING_ID_TO_TYPE = {
    2:  'enum',
    3:  'string',
    4:  'enum',
    5:  'string',
    8:  'string',
    9:  'string',
    10: 'string',
    11: 'string',
    12: 'string',
    13: 'string',
    14: 'enum',
    15: 'enum',
    16: 'enum',
    17: 'enum',
    18: 'enum',
    19: 'enum',
    20: 'enum',
    21: 'string',
    22: 'enum',
    23: 'enum',
    24: 'enum',
}

# TW_TARGETING_ID_TO_TYPE but using TW_TARGETING_ENUM_TO_ID type
TW_TARGETING_ENUM_TO_TYPE = dict((k,TW_TARGETING_ID_TO_TYPE[v]) for k,v in TW_TARGETING_ENUM_TO_ID.iteritems())

TW_TARGETING_VALUE_TYPE = {
    2:  'string',
    3:  'base10',
    4:  'base36',
    5:  'string',
    8:  'base10',
    9:  'base10',
    10: 'string',
    11: 'string',
    12: 'string',
    13: 'base36',
    14: 'base36',
    15: 'base36',
    16: 'base36',
    17: 'base10',
    18: 'base36',
    19: 'base10',
    20: 'base10',
    21: 'base10',
    22: 'base36',
    23: 'base36',
    24: 'base36',
}

TW_TARGETING_ENUM_VALUE_TYPE = dict((k,TW_TARGETING_VALUE_TYPE[v]) for k,v in TW_TARGETING_ENUM_TO_ID.iteritems())

TW_TARGETING_ID_TO_PARAM = {
    2:  'locations',
    3:  'platforms',
    4:  'devices',
    5:  'wifi_only',
    8:  'followers_of_users',
    9:  'similar_to_followers_of_users',
    10: 'broad_keywords',
    11: 'unordered_keywords',
    12: 'phrase_keywords',
    13: 'exact_keywords',
    14: 'app_store_categories',
    15: 'network_operators',
    16: 'platform_versions',
    17: 'interests',
    18: 'tailored_audiences',
    19: 'tv_genres',
    20: 'tv_channels',
    21: 'tv_shows',
    22: 'behaviors_expanded',
    23: None,
    24: 'behaviors',
}

TW_TARGETING_ENUM_TO_PARAM = dict((k,TW_TARGETING_ID_TO_PARAM[v]) for k,v in TW_TARGETING_ENUM_TO_ID.iteritems())

TW_TARGETING_TYPE = {
    'LOCATION': {
        'type': 'enum',
        'value': 2,
        'LOCATION_MAPPING': {
            'COUNTRY': 'Countries',
        },
    },
    'PLATFORM': {
        'type': 'string',
        'value': 3,
    },
    'DEVICE': {
        'type': 'enum',
        'value': 4,
    },
    'WIFI_ONLY': {
        'type': 'string',
        'value': 5,
    },
    'FOLLOWERS_OF_USER': {
        'type': 'string',
        'value': 8,
    },
    'SIMILAR_TO_FOLLOWERS_OF_USER': {
        'type': 'string',
        'value': 9,
    },
    'BROAD_KEYWORD': {
        'type': 'string',
        'value': 10,
    },
    'UNORDERED_KEYWORD': {
        'type': 'string',
        'value': 11,
    },
    'PHRASE_KEYWORD': {
        'type': 'string',
        'value': 12,
    },
    'EXACT_KEYWORD':{
        'type': 'string',
        'value': 13,
    },
    'APP_STORE_CATEGORY': {
        'type': 'enum',
        'value': 14,
    },
    'NETWORK_OPERATOR': {
        'type': 'enum',
        'value': 15,
    },
    'PLATFORM_VERSION': {
        'type': 'enum',
        'value': 16,
    },
    'INTEREST': {
        'type': 'enum',
        'value': 17,
    },
    'TAILORED_AUDIENCE': {
        'type': 'enum',
        'value': 18,
    },
    'TV_GENRE': {
        'type': 'enum',
        'value': 19,
    },
    'TV_CHANNEL': {
        'type': 'enum',
        'value': 20,
    },
    'TV_SHOW': {
        'type': 'string',
        'value': 21,
    },
    'BEHAVIOR_EXPANDED': {
        'type': 'enum',
        'value': 22,
    },
    'EVENT': {
        'type': 'enum',
        'value': 23,
    },
    'BEHAVIOR': {
        'type': 'enum',
        'value': 24,
    },

}

# +-------------------+---------------------+------+-----+---------+-------+
# | Field             | Type                | Null | Key | Default | Extra |
# +-------------------+---------------------+------+-----+---------+-------+
# | tw_line_item_id   | int(10) unsigned    | NO   | MUL | NULL    |       |
# | tw_targeting_type | tinyint(3) unsigned | NO   |     | NULL    |       |
# | tw_targeting_id   | int(10)             | YES  |     | NULL    |       |
# | targeting_value   | text                | YES  |     | NULL    |       |
# +-------------------+---------------------+------+-----+---------+-------+
