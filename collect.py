#!/usr/bin/env python3

import pymysql
import warnings

from api import API
import private

mysql = pymysql.connect(host=private.mysql_hostname,
                        user=private.mysql_user,
                        password=private.mysql_password,
                        db=private.mysql_db)

api = API(private.username, private.password)

me = api.getUser()
home = me.getHome(name=private.home)

weather = home.getWeather()
outsideTemperature = weather["outsideTemperature"]["celsius"]

for name in private.zones:
    zone = home.getZone(name=name)
    state = zone.getState()

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
