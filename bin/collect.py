#!/usr/bin/env python3

import os
import sys
import pymysql
import warnings

bindir = os.path.dirname(os.path.realpath(__file__))
root = os.path.dirname(bindir)
libdir = os.path.join(root, 'lib')
sys.path.append(libdir)

from PyTado.interface import Tado
import private

mysql = pymysql.connect(host=os.getenv('MYSQL_HOST', private.mysql_host),
                        user=os.getenv('MYSQL_USER', private.mysql_user),
                        password=os.getenv('MYSQL_PASSWORD', private.mysql_password),
                        db=os.getenv('MYSQL_DATABASE', private.mysql_database))

api = Tado(private.username, private.password)

weather = api.getWeather()
outsideTemperature = weather["outsideTemperature"]["celsius"]

zones = {zone["name"]: zone["id"] for zone in api.getZones()}

for name in private.zones:
    zone = zones[name]
    state = api.getState(zone)

    # create new table
    with warnings.catch_warnings(), mysql.cursor() as cursor:
        # temperatures are < 100 with up to two digits past the comma --> DECIMAL(4,2)
        # percentages are <= 100 with only one digit past the comma --> DECIMAL(4,1)
        sql = """
            CREATE TABLE IF NOT EXISTS `{}` (
                `timestamp` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                `outsideTemperature` DECIMAL(4,2),
                `setpoint` DECIMAL(4,2),
                `temperature` DECIMAL(4,2),
                `humidity` DECIMAL(4,1),
                `heatingpower` DECIMAL(4,1),
                PRIMARY KEY (`timestamp`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin
            AUTO_INCREMENT=1 ;
        """.format(name)
        warnings.filterwarnings('ignore', ".*Table '{}' already exists.*".format(name))
        cursor.execute(sql)

    heatingpower = state["activityDataPoints"]["heatingPower"]["percentage"]

    temperature = state["sensorDataPoints"]["insideTemperature"]["celsius"]
    humidity = state["sensorDataPoints"]["humidity"]["percentage"]

    overlay = state.get("overlay", None)
    setting = overlay["setting"] if overlay else state["setting"]
    setpoint = setting["temperature"]["celsius"] if setting["power"] == 'ON' else None

    # insert data
    with mysql.cursor() as cursor:
        sql = """
            INSERT INTO `{}`
                (outsideTemperature, setpoint, temperature, humidity, heatingpower)
                 VALUES(%s,%s,%s,%s,%s)
        """.format(name)
        cursor.execute(sql, (outsideTemperature, setpoint, temperature, humidity, heatingpower))

    mysql.commit()

mysql.close()
