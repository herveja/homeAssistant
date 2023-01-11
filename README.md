# homeAssistant
## gazpar_insert_statistics.py
Python script for home assistant; Insert a long term statistic entry (in SQL table statistics) based on Gazpar daily values. 

This sensor can be used in Energy dashboard.

Work in conjuction with gazpar sensor (https://github.com/ssenart/home-assistant-gazpar)


### fields:
* gazpar_sensor_name:
     description: Name of the sensor containing gazpar attributes. Default=sensor.gazpar
     example: sensor.gazpark
     required: false
* history_sensor_name:
     description: Name of the history sensor containing statistics. Default=gazpar_statistics
     example: gazpar_statistics
     required: false
 * domain_name:
     description: Domain name of the sensor. The sensor will be <domain_name>:<history_sensor_name>
     example: gazpar_statistics
     required: false
     
### Logic
* Each time the sensor.gazpar is changed, an automation calls the service (service: pyscript.gazpar_insert_statistics). The script checks the latest date in statistics table and insert a new line is the date (time_period in list dqily. bellow). 


```
sensor.gazpar attribute sample data
    attribution: Data provided by GrDF
    version: 1.3.4
    username: xxxxxxxxxxxxxxxxxxxxxxxx
    pce: xxxxxxxxxxxxxxxxxxxxxxxx
    unit_of_measurement: kWh
    friendly_name: Gazpar
    icon: mdi:fire
    device_class: energy
    state_class: total_increasing
    errorMessages: 
    hourly: 
    daily: 
    - time_period: 08/01/2023
      start_index_m3: 522
      end_index_m3: 526
      volume_m3: 3
      energy_kwh: 39
      converter_factor_kwh/m3: 11.2
      temperature_degC: 8.21
      type: Mesuré
      timestamp: '2023-01-11T16:09:52.818042'
    - time_period: 07/01/2023
      start_index_m3: 516
      end_index_m3: 522
      volume_m3: 6
      energy_kwh: 65
      converter_factor_kwh/m3: 11.2
      temperature_degC: 9.46
      type: Mesuré
```

based on homeassistant async_add_external_statistics
```
@callback
def async_add_external_statistics(
    hass: HomeAssistant,
    metadata: StatisticMetaData,
    statistics: Iterable[StatisticData],
) -> None:
    """Add hourly statistics from an external source.
    This inserts an import_statistics job in the recorder's queue.
    """
```

to run this script in homeassistant (from automation) I use Pyscript in HACS https://github.com/custom-components/pyscript


## gazpar_update_history.py
(OLD APPROACH)
Python script for home assistant; update SQL table 'history' based on "time_period" attribute in sensor.gazpar. 
Gazpar usualy delivers the value wuth a two or tree days delay. 
This scrip is a workarround

Work in conjuction with the following custom sensor 

**Warning : this version of the script works only with statistics 'volume of Gas in cubic meters'**

```
  - sensor:
    - name: gas_volume
      unit_of_measurement: 'm³'
      state: >
        {{ state_attr('sensor.gazpar', 'daily')[0]['end_index_m3'] | float(0) }}
      icon: mdi:fire
      device_class: gas
      state_class: total_increasing
```
