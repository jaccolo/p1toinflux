# Home Wizard P1 dongle

A wifi enabled P1 dongle to enable smart meter readings (electricity/gas) via a wifi network.  

- [Home Wizard P1 dongle](https://www.homewizard.com/nl/p1-meter/)
- [API documentation](https://homewizard-energy-api.readthedocs.io/)
- [Smart meter SMR versions](https://helpdesk.homewizard.com/nl/articles/5935311-werkt-de-p1-meter-met-mijn-slimme-meter)

# Docker container

The container uses the API of the dongle to read values of imported/exported electicity and
imported gas (when enabled).  
It reads the values for electricity every 5 seconds (SMR5) or every 15 seconds (SMR3/4).  
It reads the values for gas every 300 seconds (SMR5) or every 3600 seconds (SMR3/4).  
The readings are exported to InfluxDB and/or stdout (container logging), check variables *ENABLE_LOGGING* and *ENABLE_INFLUXDB*.  

The container uses the following variables, some are mandatory:  

Required environment variables (no defaults):  
- `INFLUXDB_HOSTNAME`: hostname or ip-address of influxdb server
- `INFLUXDB_TOKEN`: token with write-access to influxdb bucket
- `INFLUXDB_ORG`: influxdb organization
- `P1METER_HOSTNAME`: hostname or ip-address of p1 dongle

Optional environment variables:  
- `INFLUXDB_PORT`: TCP-port of InfluxDB server, default: *8086*
- `INFLUXDB_BUCKET`: bucketname to store data in InfluxDB

Optional environment variables for debugging:  
- `ENABLE_LOGGING`: *true* (log p1 data to stdout) or *false* (no p1 data to stdout, default)
- `ENABLE_INFLUXDB`: *true* (write p1 data to InfluxDB, default) or *false* (do not write to InfluxDB)

## Build the container image

```
docker build -t p1toinflux:1.0 .
```

## Run the container

Because some variables are mandatory, you can use a environment file to make
variables available to the container.  
Do NOT use single/double quotes, because the quotes will be included in the values.  

Example *envfile*:
```
# Mandatory variables
INFLUXDB_HOSTNAME=influxdb.mydomain
INFLUXDB_TOKEN=ThisTokenIsGeneratedAtTheInfluxDBhostAndGivesAccessToTheBucketToStoreP1Data
INFLUXDB_ORG=Home
P1METER_HOSTNAME=p1.mydomain
# Optional variables
#INFLUXDB_PORT=8086
#INFLUXDB_BUCKET=p1
#ENABLE_LOGGING=false
#ENABLE_INFLUXDB=true
```

Execute the container with:
```
docker run -d --env-file envfile p1toinflux:1.0
```

## Python requirements

Version:  
- >= 3.x
- tested with 3.9.2

Modules:
- influxdb-client
