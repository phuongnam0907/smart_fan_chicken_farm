#!/usr/bin/python3

import os
import glob
import time
import json
from datetime import datetime
import paho.mqtt.client as mqtt

import RPi.GPIO as GPIO

# ================== CONFIGURATION ================== #
BASE_DIR = '/sys/bus/w1/devices/'
DEVICE_DIR = glob.glob(BASE_DIR + '28*')[0]
DEVICE_FILE = DEVICE_DIR + '/w1_slave'

IO_CONTROL_PIN_25_MAP_TO_GPIO = 26
IO_CONTROL_PIN_28_MAP_TO_GPIO = 20
IO_CONTROL_PIN_29_MAP_TO_GPIO = 21

TEMPERATURE_TURN_ON_FAN = 50
TEMPERATURE_TURN_OFF_FAN = 30

STATION_ID = "STATION_ID_001"
STATION_NAME = "TRẠM 001"

MQTT_USERNAME = "smart_fan"
MQTT_PASSWORD = "SmartFan_MrArxZ8mmM"
MQTT_HOST = "mqttserver.tk"
MQTT_PORT = 1883
MQTT_TOPIC = "/industrial_fan_ht/smart_fan/" + STATION_ID + "/"
MQTT_TOPIC_STATUS = MQTT_TOPIC + "status"
MQTT_TOPIC_CONFIG = MQTT_TOPIC + "config"
MQTT_TOPIC_FAN = MQTT_TOPIC + "fan"

data_payload = {"project_id": "SMARTFAN", "project_name": "SMART FAN", "station_id": "STATION_ID_XXX",
                "station_name": "STATION_NAME_XXX", "longitude": 106.660172, "latitude": 10.762622,
                "volt_battery": 12.2, "volt_solar": 5.3}
data_status = [{"ss_name": "fan_temperature", "ss_unit": "0C", "ss_value": 0},
               {"ss_name": "temperature_max", "ss_unit": "0C", "ss_value": 30.3},
               {"ss_name": "temperature_min", "ss_unit": "0C", "ss_value": 20.25},
               {"ss_name": "mode_fan_auto", "ss_unit": "", "ss_value": 1},
               {"ss_name": "fan_status", "ss_unit": "", "ss_value": 1}]
data_config = {"temperature_max": 30.3, "temperature_min": 20.25, "mode_fan_auto": 1}
data_fan_control = {"fan_status": 1}

fan_status = 0
temp_max = 32.00
temp_min = 20.25
mode_auto = 1
cur_temp = 0
cur_humi = 0


# ================ FUNCTIONS DEFINE ================= #
def setup_environment():
    global DEVICE_DIR
    os.system('modprobe w1-gpio')
    os.system('modprobe w1-therm')
    
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(IO_CONTROL_PIN_25_MAP_TO_GPIO, GPIO.OUT)
    GPIO.setup(IO_CONTROL_PIN_28_MAP_TO_GPIO, GPIO.OUT)
    GPIO.setup(IO_CONTROL_PIN_29_MAP_TO_GPIO, GPIO.OUT)


def read_temp_raw():
    f = open(DEVICE_FILE, 'r')
    lines = f.readlines()
    f.close()
    return lines


def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2:]
        temp_c = float(temp_string) / 1000.0
        return round(temp_c, 2)


def control_gpio(pin25=None, pin28=None, pin29=None):
    if pin25 is not None:
        if pin25 is True:
            GPIO.output(IO_CONTROL_PIN_25_MAP_TO_GPIO, GPIO.HIGH)
        else:
            GPIO.output(IO_CONTROL_PIN_25_MAP_TO_GPIO, GPIO.LOW)
    if pin28 is not None:
        if pin25 is True:
            GPIO.output(IO_CONTROL_PIN_28_MAP_TO_GPIO, GPIO.HIGH)
        else:
            GPIO.output(IO_CONTROL_PIN_28_MAP_TO_GPIO, GPIO.LOW)
    if pin29 is not None:
        if pin25 is True:
            GPIO.output(IO_CONTROL_PIN_29_MAP_TO_GPIO, GPIO.HIGH)
        else:
            GPIO.output(IO_CONTROL_PIN_29_MAP_TO_GPIO, GPIO.LOW)
    pass


def fan_control(status):
    print("DEBUG: Status of fan", status)
    if status == 1:
        control_gpio(True, True, True)
    else:
        control_gpio(False, False, False)


def on_connect(client, userdata, rc, *extra_params):
    print('Connected with result code ' + str(rc))
    client.subscribe(MQTT_TOPIC_CONFIG)
    client.subscribe(MQTT_TOPIC_FAN)
    pass


def on_message(client, userdata, msg):
    global fan_status, temp_max, temp_min, mode_auto
    print("Receive message: ", msg.payload)
    try:
        jsonObject = json.loads(msg.payload)
        if msg.topic == MQTT_TOPIC_FAN:
            if jsonObject["device_status"] == 0:
                data_fan_control["fan_status"] = jsonObject["fan_status"]
                data_fan_control["device_status"] = 1
                if mode_auto == 0:
                    fan_status = jsonObject["fan_status"]
                    fan_control(fan_status)
                client.publish(MQTT_TOPIC_FAN, json.dumps(data_fan_control), 0, 1)

        elif msg.topic == MQTT_TOPIC_CONFIG:
            if jsonObject["temperature_max"] is not None:
                temp_max = jsonObject["temperature_max"]
            if jsonObject["temperature_min"] is not None:
                temp_min = jsonObject["temperature_min"]
            if jsonObject["mode_fan_auto"] is not None:
                mode_auto = jsonObject["mode_fan_auto"]

            data_payload['station_id'] = STATION_ID
            data_payload['station_name'] = STATION_NAME
            data_status[0]["ss_value"] = read_temp()
            data_status[1]["ss_value"] = temp_max
            data_status[2]["ss_value"] = temp_min
            data_status[3]["ss_value"] = mode_auto
            data_status[4]["ss_value"] = fan_status
            data_payload['data_ss'] = data_status
            data_payload['device_status'] = 1
            client.publish(MQTT_TOPIC_STATUS, json.dumps(data_payload), 0, 1)
    except:
        print("An exception occurred")


# =================== START MAIN ==================== #
if __name__ == '__main__':
    setup_environment()

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.connect(MQTT_HOST, MQTT_PORT)
    client.loop_start()
    fan_control(0)
    timer = 0

    time.sleep(5)

    while True:
        cur_temp = read_temp()
        print("DEBUG: Current temperature", cur_temp, "| Max", temp_max, "| Min", temp_min)

        if mode_auto == 1:
            if cur_temp >= temp_max:
                fan_status = 1
            if cur_temp <= temp_min:
                fan_status = 0
            fan_control(fan_status)

        if timer >= 60:
            data_payload['station_id'] = STATION_ID
            data_payload['station_name'] = STATION_NAME
            data_status[0]["ss_value"] = cur_temp
            data_status[1]["ss_value"] = temp_max
            data_status[2]["ss_value"] = temp_min
            data_status[3]["ss_value"] = mode_auto
            data_status[4]["ss_value"] = fan_status
            data_payload['data_ss'] = data_status
            data_payload['device_status'] = 0
            print("DEBUG: Publish data", json.dumps(data_payload))
            client.publish(MQTT_TOPIC_STATUS, json.dumps(data_payload), 0, 1)
            timer = 0

        time.sleep(1)
        timer += 1
