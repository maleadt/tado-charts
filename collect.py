#!/usr/bin/env python3

import json
import urllib.request
import urllib.parse
import urllib.error
import pymysql

import private


## wrappers

class API:
    def __login(self, username, password):
        args = urllib.parse.urlencode({
            'client_id': 'tado-webapp',
            'grant_type': 'password',
            'scope': 'home.user',
            'username': username,
            'password': password
        })
        req = urllib.request.Request('{}://{}/oauth/token'.format(self.scheme, self.server), args.encode())
        res = urllib.request.urlopen(req)
        raw_data = res.read().decode()
        data = json.loads(raw_data)
        return data

    def __authorize(self, req):
        req.add_header("Authorization", "{} {}".format(self.token['token_type'], self.token['access_token']))

    def __init__(self, username, password, server="my.tado.com", scheme="https"):
        self.server = server
        self.scheme = scheme
        self.token = self.__login(username, password)

    def get(self, resource):
        req = urllib.request.Request('{}://{}/api/v2{}'.format(self.scheme, self.server, resource))
        self.__authorize(req)
        res = urllib.request.urlopen(req)
        raw_data = res.read().decode()
        data = json.loads(raw_data)
        return data

    def getUser(self):
        return User(self)


class User:
    def __init__(self, api):
        self.api = api
        self.data = api.get("/me")

    def getHomes(self):
        return list(map(lambda home: Home(self.api, home), self.data["homes"]))

    def getHome(self, **kwargs):
        homes = self.data["homes"]
        if "id" in kwargs:
            home = list(filter(lambda home: home["id"] == kwargs["id"], homes))
        elif "name" in kwargs:
            home = list(filter(lambda home: home["name"] == kwargs["name"], homes))
        else:
            raise ValueError("getHome expects name or id")
        if len(home) == 0:
            return None
        elif len(home) > 1:
            raise ValueError("multiple zones matching given name or id")
        return Home(self.api, home[0])


class Home:
    def __init__(self, api, data):
        self.api = api
        self.data = api.get("/homes/{}".format(data["id"]))

    def getWeather(self):
        return self.api.get("/homes/{}/weather".format(self.data["id"]))

    def getDevices(self):
        return self.api.get("/homes/{}/devices/".format(self.data["id"]))

    def getMobileDevices(self):
        return self.api.get("/homes/{}/mobileDevices/".format(self.data["id"]))

    def getInstallations(self):
        return self.api.get("/homes/{}/installations/".format(self.data["id"]))

    def getUsers(self):
        return self.api.get("/homes/{}/users/".format(self.data["id"]))

    def getZones(self):
        zones = self.api.get("/homes/{}/zones/".format(self.data["id"]))
        return list(map(lambda zone: Zone(self.api, self, zone), zones))

    def getZone(self, **kwargs):
        zones = self.api.get("/homes/{}/zones/".format(self.data["id"]))
        if "id" in kwargs:
            zone = list(filter(lambda zone: zone["id"] == kwargs["id"], zones))
        elif "name" in kwargs:
            zone = list(filter(lambda zone: zone["name"] == kwargs["name"], zones))
        else:
            raise ValueError("getZone expects name or id")
        if len(zone) == 0:
            return None
        elif len(zone) > 1:
            raise ValueError("multiple zones matching given name or id")
        return Zone(self.api, self, zone[0])


class Zone:
    def __init__(self, api, home, data):
        self.api = api
        self.home = home
        self.data = data

    def getCapabilities(self):
        return self.api.get("/homes/{}/zones/{}/capabilities".format(self.home.data["id"], self.data["id"]))

    def getState(self):
        return self.api.get("/homes/{}/zones/{}/state".format(self.home.data["id"], self.data["id"]))

    def getDevices(self):
        return list(map(lambda device: Device(self.api, self, device), self.data["devices"]))


class Device:
    def __init__(self, api, zone, data):
        self.api = api
        self.zone = zone
        self.data = data


## main

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

    heatingpower = state["activityDataPoints"]["heatingPower"]["percentage"]

    temperature = state["sensorDataPoints"]["insideTemperature"]["celsius"]
    humidity = state["sensorDataPoints"]["humidity"]["percentage"]

    overlay = state.get("overlay", None)
    setting = overlay["setting"] if overlay else state["setting"]
    setpoint = setting["temperature"]["celsius"] if setting["power"] == 'ON' else None

    with mysql.cursor() as cursor:
        sql = """
            INSERT INTO `{}`
                (outsideTemperature, setpoint, temperature, humidity, heatingpower)
                 VALUES(%s,%s,%s,%s,%s)
        """.format(name)
        cursor.execute(sql, (outsideTemperature, setpoint, temperature, humidity, heatingpower))

    mysql.commit()

mysql.close()
