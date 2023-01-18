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

sample Automation to fire the script each time gazpar sensor is updated
```
alias: "[gazpar] Insert Statistics"
description: ""
trigger:
  - platform: state
    entity_id:
      - sensor.gazpar
condition: []
action:
  - service: pyscript.gazpar_insert_statistics
    data:
      gazpar_sensor_name: sensor.gazpar
      history_sensor_name: gazpar_statistics
      domain_name: gazpar
      volume_or_energy: energy
  - service: pyscript.gazpar_insert_statistics
```

To run this script in homeassistant (from automation) I use Pyscript in HACS https://github.com/custom-components/pyscript

This python script is using homeassistant internal methode async_add_external_statistics (https://github.com/home-assistant/core/pull/56607)
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


## myenedis_insert_statistics.py

Same as gazpar_insert_statistics.py but for MyEnedis (https://github.com/saniho/apiEnedis). Create long-term statistics based on dailyweek, dailyweek_HP, dailyweek_HC attribute of sensor.myenedis_xxxxxxxx so that the power consumption is accurately reported to the exact day in Energy dashboard 

## gazpar_update_history.py
(OLD APPROACH)(DECREPATED)
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
