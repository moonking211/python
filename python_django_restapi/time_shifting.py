from datetime import datetime
from datetime import timedelta
from django.db import connection
from pytz import UTC


class PacificTimeShift(object):
    DB_SHIFT = None

    @classmethod
    def get(cls, date=None):
        if date is None:
            date = datetime.now(UTC)
        else:
            date = date.astimezone(UTC) if date.tzinfo else UTC.localize(date)

        pdt_start = date.replace(month=3, day=15, hour=9, minute=0, second=0)
        pdt_start -= timedelta(days=pdt_start.weekday() + 1)

        pdt_finish = date.replace(month=11, day=8, hour=8, minute=59, second=59)
        pdt_finish -= timedelta(days=pdt_finish.weekday() + 1)

        shift = -7 if pdt_start <= date <= pdt_finish else -8
        return shift

    @classmethod
    def get_for_db(cls):
        if cls.DB_SHIFT is None:
            cursor = connection.cursor()
            cursor.execute("SELECT TIMESTAMPDIFF(HOUR, UTC_TIMESTAMP(), NOW())")
            row = cursor.fetchone()
            cls.DB_SHIFT = row[0]
        return cls.DB_SHIFT
