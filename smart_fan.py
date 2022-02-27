#!/usr/bin/python3

import os
import glob
import time
import json
import paho.mqtt.client as mqtt
# import RPi.GPIO as GPIO

# ================== CONFIGURATION ================== #
BASE_DIR = '/sys/bus/w1/devices/'
DEVICE_DIR = 'Get From setup_environment() function.'
DEVICE_FILE = DEVICE_DIR + '/w1_slave'

IO_CONTROL_PIN_25_MAP_TO_GPIO = 26
IO_CONTROL_PIN_28_MAP_TO_GPIO = 20
IO_CONTROL_PIN_29_MAP_TO_GPIO = 21

TEMPERATURE_TURN_ON_FAN = 50
TEMPERATURE_TURN_OFF_FAN = 30

STATION_ID = "STATION_ID_001"
STATION_NAME ="STATION_NAME_001"

MQTT_USERNAME = "smart_fan"
MQTT_PASSWORD = "IndustrySmartFanHT"
MQTT_HOST = "mqttserver.tk"
MQTT_PORT = 1883
MQTT_TOPIC = "/industrial_fan_ht/smart_fan/" + STATION_ID + "/"
MQTT_TOPIC_STATUS = MQTT_TOPIC + "status"
MQTT_TOPIC_CONFIG = MQTT_TOPIC + "config"
MQTT_TOPIC_FAN = MQTT_TOPIC + "fan"

data_payload = {"project_id":"SMARTFAN","project_name":"SMART FAN","station_id":"STATION_ID_XXX","station_name":"STATION_NAME_XXX","longitude":106.660172,"latitude":10.762622,"volt_battery":12.2,"volt_solar":5.3}
data_status = [{"ss_name":"fan_temperature","ss_unit":"0C","ss_value":0},{"ss_name":"fan_humidity","ss_unit":"%","ss_value":0},{"ss_name":"temperature_on","ss_unit":"0C","ss_value":30.3},{"ss_name":"temperature_off","ss_unit":"0C","ss_value":20.25},{"ss_name":"mode_fan_auto","ss_unit":"","ss_value":1},{"ss_name":"fan_status","ss_unit":"","ss_value":1}]
data_config = {"temperature_on":30.3,"temperature_off":20.25,"mode_fan_auto":1}
data_fan_control = {"fan_status":1}

# ================ FUNCTIONS DEFINE ================= #
def setup_environment():
    global DEVICE_DIR
    os.system('modprobe w1-gpio')
    os.system('modprobe w1-therm')
    DEVICE_DIR = glob.glob(BASE_DIR + '28*')[0]

    # GPIO.setup(IO_CONTROL_PIN_25_MAP_TO_GPIO, GPIO.OUT)
    # GPIO.setup(IO_CONTROL_PIN_28_MAP_TO_GPIO, GPIO.OUT)
    # GPIO.setup(IO_CONTROL_PIN_29_MAP_TO_GPIO, GPIO.OUT)


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
        return temp_c


def get_status(fan_status):

    pass

def control_gpio(pin25=None, pin28=None, pin29=None):
    # if pin25 is not None:
    #     if pin25 is True:
    #         GPIO.output(IO_CONTROL_PIN_25_MAP_TO_GPIO, GPIO.HIGH)
    #     else:
    #         GPIO.output(IO_CONTROL_PIN_25_MAP_TO_GPIO, GPIO.LOW)
    #     time.sleep(0.5)
    # if pin28 is not None:
    #     if pin25 is True:
    #         GPIO.output(IO_CONTROL_PIN_28_MAP_TO_GPIO, GPIO.HIGH)
    #     else:
    #         GPIO.output(IO_CONTROL_PIN_28_MAP_TO_GPIO, GPIO.LOW)
    #     time.sleep(0.5)
    # if pin29 is not None:
    #     if pin25 is True:
    #         GPIO.output(IO_CONTROL_PIN_29_MAP_TO_GPIO, GPIO.HIGH)
    #     else:
    #         GPIO.output(IO_CONTROL_PIN_29_MAP_TO_GPIO, GPIO.LOW)
    #     time.sleep(0.5)
    pass


def fan_control(status):
    print("Status of fan:", status)
    if status is True:
        control_gpio(True, True, True)
    else:
        control_gpio(False, False, False)


def on_connect(client, userdata, rc, *extra_params):
    print('Connected with result code ' + str(rc))
    client.subscribe(MQTT_TOPIC_CONFIG)
    client.subscribe(MQTT_TOPIC_FAN)
    pass


def on_message(client, userdata, msg):
    print("Receive message: ", msg.payload)


# =================== START MAIN ==================== #
if __name__ == '__main__':
    # setup_environment()

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.connect(MQTT_HOST, MQTT_PORT)
    client.loop_start()
    fan_status = False

    while True:
        # print(read_temp())
        print("this is value:", 28.875)
        data_payload['station_id'] = STATION_ID
        data_payload['station_name'] = STATION_NAME
        data_payload['data_ss'] = data_status
        data_payload['device_status'] = 0
        data_fan_control['device_status'] = 0
        client.publish(MQTT_TOPIC_FAN, json.dumps(data_fan_control), 0, 1)
        client.publish(MQTT_TOPIC_STATUS, json.dumps(data_payload), 0, 1)
        print(MQTT_TOPIC_STATUS)
        print(data_payload)
        print()
        print(MQTT_TOPIC_CONFIG)
        print(data_config)
        print()
        print(MQTT_TOPIC_FAN)
        print(data_fan_control)
        time.sleep(10)