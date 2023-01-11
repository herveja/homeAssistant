import homeassistant.components.recorder
from homeassistant.const import (UnitOfEnergy)
from homeassistant.components.recorder.models import StatisticData, StatisticMetaData
from homeassistant.components.recorder.statistics import (
    get_last_statistics,
    async_add_external_statistics
    )
import datetime
import logging


#################
# Helper classes
################# 
_LOGGER = logging.getLogger(__name__)

class DAILY_STAT:
    HOUR = 20
    MIN = 0
    SEC = 0


@service
async def gazpar_insert_statistics(history_sensor_name = 'gazpar_statistics', gazpar_sensor_name = 'sensor.gazpar', domain_name='gazpar'):
    """yaml
name: gazpar_insert_statistics
description: Insert a long term statistic entry based on Gazpar daily values. 
fields:
  gazpar_sensor_name:
     description: Name of the sensor containing gazpar attributes. Default=sensor.gazpar
     example: sensor.gazpark
     required: false
  history_sensor_name:
     description: Name of the history sensor containing statistics. Default=gazpar_statistics
     example: gazpar_statistics
     required: false
  domain_name:
     description: Domain name of the sensor. The sensor will be <domain_name>:<history_sensor_name>
     example: gazpar_statistics
     required: false
"""    
    # Hassio task name
    task.unique("gazpar_insert_statistics")
     
    delta_attribute = "energy_kwh"

    statistic_id = f"{domain_name}:{history_sensor_name}".lower()

    last_stats = await homeassistant.components.recorder.get_instance(hass).async_add_executor_job(
        get_last_statistics, hass, 1, statistic_id, True, {'state','sum'}
        )
    
    last_sum = 0
    last_date = datetime.datetime(year=1900, month=1, day=1,hour=0, minute=0, second=0, microsecond=0, tzinfo=datetime.timezone.utc)

    if (last_stats is not None):
        if (len(last_stats) != 0):
            last_sum = last_stats[statistic_id][0]['sum']
            if (last_sum is not None):
                last_sum = int(last_sum)
                last_date = last_stats[statistic_id][0]['start']

    _LOGGER.info(f"[****GAZPAR****] LAST SUM={last_sum} LAST_DATE={last_date} ")
    _LOGGER.info(f"[****GAZPAR****] ------------------------")

    try:
        daily = state.get(f"{gazpar_sensor_name}.daily")
    except:
        _LOGGER.error(f"[****GAZPAR****]  Error: gazpar sensor not found (sensor.gazpar.daily) ")
        return

    # prepare list of stat to be inserted
    metadata = StatisticMetaData(has_mean=False, has_sum=True, 
                name=history_sensor_name,
                source=domain_name,
                statistic_id=statistic_id,
                unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR )

    statistics = []

    # Sort time_period desc
    sorted_list = sorted(daily , key=lambda t: datetime.datetime.strptime(t['time_period'], '%d/%m/%Y'))
    dtTimePeriod = ""
    
    # Update statistics by date
    for d in sorted_list:
        # date
        dtTimePeriod = d["time_period"]
        dtsplit = dtTimePeriod.split('/')
        dt = datetime.datetime(year=int(dtsplit[2]), month=int(dtsplit[1]), day=int(dtsplit[0]), 
            hour=DAILY_STAT.HOUR, minute=DAILY_STAT.MIN, second=DAILY_STAT.SEC, microsecond=0, 
            tzinfo=datetime.timezone.utc)

        if (dt > last_date):
            # state & sum
            new_state = d[delta_attribute]
            last_sum += new_state
            new_sum = last_sum

            _LOGGER.info(f"[****GAZPAR****] Daily Date={dt} Delta={new_state} sum={new_sum} ")
            # add to list
            statistics.append(StatisticData(start=dt, state=new_state, sum=new_sum))
        else:
            _LOGGER.info(f"[****GAZPAR****] Date skipped {dt} ")

    if (len(statistics)>0):       
       _LOGGER.info(f"adding {len(statistics)} statistics for column {statistic_id}")
       async_add_external_statistics(hass , metadata, statistics)

    _LOGGER.info(f"[****GAZPAR****] --------THE---END-------")
