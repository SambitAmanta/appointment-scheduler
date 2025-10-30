from datetime import datetime, timedelta, date

def date_range(start_date, end_date):
    cur = start_date
    while cur <= end_date:
        yield cur
        cur += timedelta(days=1)
