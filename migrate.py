#!/usr/bin/env python3

import os
import sys
import csv
import pytz
import numpy as np
import dateutil.parser
import pymysql
import progressbar

import private

mysql = pymysql.connect(host=private.mysql_hostname,
                        user=private.mysql_user,
                        password=private.mysql_password,
                        db=private.mysql_db)

for zone in private.zones:
    print("Migrating data for zone {}".format(zone))

    # drop existing table
    with mysql.cursor() as cursor:
        sql = "DROP TABLE IF EXISTS {}".format(zone)
        cursor.execute(sql)

    # create new table
    with mysql.cursor() as cursor:
        # temperatures are < 100 with up to two digits past the comma --> DECIMAL(4,2)
        # percentages are <= 100 with only one digit past the comma --> DECIMAL(4,1)
        sql = """
            CREATE TABLE `{}` (
                `timestamp` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                `outsideTemperature` DECIMAL(4,2),
                `setpoint` DECIMAL(4,2),
                `temperature` DECIMAL(4,2),
                `humidity` DECIMAL(4,1),
                `heatingpower` DECIMAL(4,1),
                PRIMARY KEY (`timestamp`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin
            AUTO_INCREMENT=1 ;
        """.format(zone)
        cursor.execute(sql)

    # parse and import data
    with mysql.cursor() as cursor:
        sql = """REPLACE INTO `{}`
                 VALUES(CONVERT_TZ(%s,'+00:00',@@session.time_zone),%s,%s,%s,%s,%s)
              """.format(zone)

        dirname = os.path.dirname(sys.argv[0])
        csv_path = "{}/{}.csv".format(dirname, zone)
        csv_reader = csv.reader(open(csv_path))
        csv_lines = sum(1 for line in open(csv_path))

        with progressbar.ProgressBar(max_value=csv_lines) as bar:
            line_index = 0
            for line in csv_reader:
                line_index = line_index+1
                bar.update(line_index)

                timestamp = pytz.utc.localize(dateutil.parser.parse(line.pop(0)))
                values = np.array(list(map(float, line)))
                values = np.where(np.isnan(values), None, values)

                # pprint.pprint((timestamp, *values))
                cursor.execute(sql, (timestamp, *values))

    mysql.commit()

mysql.close()
