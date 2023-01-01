# homeAssistant
## gazpar_update_history.py
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

to run this script in homeassistant (from automation) I use Pyscript in HACS https://github.com/custom-components/pyscript
