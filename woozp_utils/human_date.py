from datetime import datetime


def _tag_value(value, name, extra=''):
    s = ''
    if value == 1:
        s = 'one ' + name + extra
    elif value > 1:
        s = '%d %ss' % (value, name) + extra
    return s



def to_human_date(date):
    _date = datetime(*date.timetuple()[:6])# this is in case we get a date object instead of a datetime
    s = ''
    ago = ' ago'
    err_date = 'on ' + date.strftime('%B %d, %Y')
    now = datetime.now()
    today_beg = datetime(now.year, now.month, now.day)
    date_beg = datetime(_date.year, _date.month, _date.day)
    years = today_beg.year - date_beg.year
    months = today_beg.month - date_beg.month
    if months < 0:
        years = years - 1
        months = months + 12
    if months < 0 or years < 0: # this shouldn't ever happen
        return err_date
    if months > 1 or years > 0:
        s = _tag_value(years, 'year', '')
        if years <= 1:
            if years > 0 and months > 0:
                s = s + ', '
            s = s + _tag_value(months, 'month', '')
        return s + ago
    
    if date_beg < today_beg: 
        delta = today_beg - date_beg
        days = delta.days
        if days == 1:
            return 'yesterday'
        if days > 1 and days <= 6:
            return _date.strftime('last %A')
        if days > 6:
            return _tag_value(days, 'day', ago)
    else:
        delta = now - _date
        if delta.days < 0: # this shouldn't ever happen
            return err_date
        hours = delta.seconds // 3600
        if hours > 0:
            return _tag_value(hours, 'hour', ago)
        minutes = delta.seconds % 3600 // 60
        if minutes > 0:
            return _tag_value(minutes, 'minute', ago)
        seconds = delta.seconds % 3600 % 60
        if seconds > 0:
            return _tag_value(seconds, 'second', ago)
        return 'just right now'


def human_date2(date):
    err_date = 'on ' + date.strftime('%B %d, %Y')
    now = datetime.now()
    today_beg = datetime(now.year, now.month, now.day)
    date_beg = datetime(date.year, date.month, date.day)
    delta = today_beg - date_beg
    if delta.days > 1:
        return date.strftime('%m/%d/%Y, %I:%M %p')
    elif delta.days > 0:
        return date.strftime('Yesterday, %I:%M %p')
    return date.strftime('%I:%M %p')
    
