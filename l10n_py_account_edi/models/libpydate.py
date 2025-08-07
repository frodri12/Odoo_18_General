#

from datetime import datetime
from zoneinfo import ZoneInfo
import pytz

### Convierte un string en formato 2019-03-01T10:23:53-03:00
### a un string UTC en formato 2019-03-01T13:23:53
### Solo esta soportado -03:00 y -04:00
def from_date2utc(date):
    d1 = date.split("T")[0]
    d2 = date.split("T")[1]
    d3 = d2[8:]
    d2 = d2[0:8]
    tzname = 'UTC'
    if d3 == '-03:00':
        tzname = 'America/Buenos_Aires'
    elif d3 == '-04:00':
        tzname = 'America/Asuncion'
    dt = datetime.strptime(d1 + " " + d2, "%Y-%m-%d %H:%M:%S").replace(tzinfo=ZoneInfo(tzname))
    return dt.astimezone(ZoneInfo('UTC')).isoformat(timespec='seconds').replace("+00:00", "")

def from_date2tz( moveId, date, timezone=None):
    now = date
    if not date or date == None:
        now = datetime.now()
    if not timezone or timezone == None:
        user = moveId.env['res.users'].browse([2])
        tz = pytz.timezone(user.tz) or pytz.utc
    else:
        tz = pytz.timezone(timezone) or pytz.utc
    user_tz = pytz.utc.localize(now).astimezone(tz)
    #return user_tz.strftime("%Y-%m-%dT%H:%M:%S") #A004
    return user_tz
