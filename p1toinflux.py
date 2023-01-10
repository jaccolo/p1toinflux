#!/usr/bin/env python3
#
# API docs: https://homewizard-energy-api.readthedocs.io/
#
# Required environment variables (no defaults):
# - INFLUXDB_HOSTNAME: hostname or ip-address of influxdb server
# - INFLUXDB_TOKEN: token with read-access to influxdb bucket
# - INFLUXDB_ORG: influxdb organization
# - P1METER_HOSTNAME: hostname or ip-address of p1 dongle
# Optional environment variables:
# - INFLUXDB_PORT: TCP-port of InfluxDB server, default: 8086
# - INFLUXDB_BUCKET: bucketname to store data in InfluxDB
# Optional environment variables for debugging:
# - ENABLE_LOGGING: true (log p1 data to stdout) or false (no p1 data to stdout, default)
# - ENABLE_INFLUXDB: true (write p1 data to InfluxDB, default) or false (do not write to InfluxDB)

import os
import sys
import time
import json
import urllib.request
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

def determine_interval(p1meter):

    # Information about update intervals for current and gas for different types:
    # https://helpdesk.homewizard.com/nl/articles/5935311-werkt-de-p1-meter-met-mijn-slimme-meter
    try:
        p1data  = urllib.request.urlopen(f"http://{p1meter}/api/v1/data")
    except Exception as e:
        print(f"Error reading from p1meter {p1meter}: {e}", file=sys.stderr)
        sys.exit(1)

    smr_version = json.loads(p1data.read().decode('ascii'))['smr_version']
    if int(smr_version) < 50:
        # SMR 3 & 4: 10 seconds electricity interval, 60 minutes gas interval
        current = 15
        gas = 3600
    else:
        # SMR 5: 1 second electricity interval, 5 minutes gas interval
        current = 5
        gas = 300

    return(current,gas)


def read_p1(p1meter):
    try:
        p1data  = urllib.request.urlopen(f"http://{p1meter}/api/v1/data")
        return(p1data)
    except Exception as e:
        print(f"Warning: error reading from p1meter {p1meter}: {e}", file=sys.stderr)


def write_influx(influxserver, influxport, influxorg, influxtoken,influxbucket, write_gas, enable_logging, enable_influxdb, p1data):

    if enable_influxdb == "TRUE":
        try:
            influxdbclient = InfluxDBClient(url=f"http://{influxserver}:{influxport}", token=influxtoken, org=influxorg)
            write_api = influxdbclient.write_api(write_options=SYNCHRONOUS)
        except Exception as e:
            print(f"Fatal error accessing InfluDB: {e}", file=sys.stderr)

    data = json.loads(p1data.read().decode('ascii'))

    if enable_logging == "TRUE":
        print(f"wifi_strength: {data['wifi_strength']}")
        print(f"total_power_import_t1_kwh: {data['total_power_import_t1_kwh']}")
        print(f"total_power_import_t2_kwh: {data['total_power_import_t2_kwh']}")
        print(f"total_power_export_t1_kwh: {data['total_power_export_t1_kwh']}")
        print(f"total_power_export_t2_kwh: {data['total_power_export_t2_kwh']}")
        print(f"active_power_w: {data['active_power_w']}")
        print(f"active_power_l1_w: {data['active_power_l1_w']}")
        print(f"active_power_l2_w: {data['active_power_l2_w']}")
        print(f"active_power_l3_w: {data['active_power_l3_w']}")

    if enable_influxdb == "TRUE":
        _p1 = Point("wifi_strength").field("percentage", data['wifi_strength'])
        _p2 = Point("total_power_import_t1_kwh").field("kwh", data['total_power_import_t1_kwh'])
        _p3 = Point("total_power_import_t2_kwh").field("kwh", data['total_power_import_t2_kwh'])
        _p4 = Point("total_power_export_t1_kwh").field("kwh", data['total_power_export_t1_kwh'])
        _p5 = Point("total_power_export_t2_kwh").field("kwh", data['total_power_export_t2_kwh'])
        _p6 = Point("active_power_w").field("watt", data['active_power_w'])
        _p7 = Point("active_power_l1_w").field("watt", data['active_power_l1_w'])
        _p8 = Point("active_power_l2_w").field("watt", data['active_power_l2_w'])
        _p9 = Point("active_power_l3_w").field("watt", data['active_power_l3_w'])
        _p10 = Point("active_power_w").field("watt", data['active_power_w'])
        write_api.write(bucket=influxbucket, org=influxorg, record=[_p1, _p2, _p3, _p4, _p5, _p6, _p7, _p8, _p9, _p10])

    if write_gas:

        if enable_logging == "TRUE":
            print(f"total_gas_m3: {data['total_gas_m3']}")
            print(f"gas_timestamp: {data['gas_timestamp']}")

        if enable_influxdb == "TRUE":
            _p12 = Point("total_gas_m3").field("m3", data['total_gas_m3'])
            _p13 = Point("gas_timestamp").field("timestamp", data['gas_timestamp'])
            write_api.write(bucket=influxbucket, org=influxorg, record=[_p12, _p13])

    if enable_influxdb == "TRUE":
        influxdbclient.__del__()


def main():

    # Required environment variables
    try:
        influxserver = os.environ['INFLUXDB_HOSTNAME']
        influxorg = os.environ['INFLUXDB_ORG']
        influxtoken = os.environ['INFLUXDB_TOKEN']
        p1meter = os.environ['P1METER_HOSTNAME']
    except KeyError as e:
        print(f"Fatal error: variable not set: {e}", file=sys.stderr)
        sys.exit(1)

    # Variables with a default value
    influxport = os.environ.get('INFLUXDB_PORT', 8086)
    influxbucket = os.environ.get('INFLUXDB_BUCKET', 'p1')
    enable_logging = str(os.environ.get('ENABLE_LOGGING', 'false')).upper()
    enable_influxdb = str(os.environ.get('ENABLE_INFLUXDB', 'true')).upper()

    current_sleep, gas_sleep = determine_interval(p1meter)
    gas_maxcounter = int(gas_sleep/current_sleep)
    gas_counter = gas_maxcounter

    while True:

        # Write gas readings not every run to influxdb, because the gas readings
        # are not updated as frequently as current readings
        if gas_counter >= gas_maxcounter:
            gas_counter = 1
            write_gas = True
        else:
            gas_counter += 1
            write_gas = False

        try:
            p1data = read_p1(p1meter)
            write_influx(influxserver, influxport, influxorg, influxtoken, influxbucket, write_gas, enable_logging, enable_influxdb, p1data)
        except Exception as e:
            print(f"Warning: error reading from p1meter {p1meter}: {e}", file=sys.stderr)
        time.sleep(current_sleep)


if __name__ == "__main__":
    main()

