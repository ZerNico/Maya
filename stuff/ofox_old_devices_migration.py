import ujson
import datetime

from maya_bot import mongodb

load = True

if load is True:
    with open('maya_bot/update.json', 'r') as f:
        data = ujson.load(f)
        load_type = 'stable'

        for codename in data[load_type]:
            device = data[load_type][codename]

            date_int = int(round(datetime.datetime.strptime(device['modified'], "%Y%m%d%H%M%S").timestamp()))

            new = {
                'codename': codename,
                'fullname': device['fullname'],
                'maintainer': device['maintainer'],
                f'{load_type}_build': device['ver'],
                f'{load_type}_date': date_int,
                f'{load_type}_changelog': device['changelog'],
                f'{load_type}_migrated': True,
            }

            mongodb.ofox_devices.update_one({'codename': codename}, {'$set': new}, upsert=True)
