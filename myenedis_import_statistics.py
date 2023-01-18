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


def get_attribute(sensor_attribute) -> str:
    ret = None
    _LOGGER.debug(f"get sensor attribut {sensor_attribute} ")
    try:
        ret = state.get(sensor_attribute)
    except:
        _LOGGER.error(f" Error: attribute not found ({sensor_attribute}) ")
        return
    return ret

#################
# myenedis_import_statistics
################# 
@service
async def myenedis_import_statistics(
        history_sensor_name = 'myenedis_statistics', 
        myenedis_sensor_name = 'sensor.myenedis_xxxxxxx', 
        domain_name='myenedis'):
    """yaml
name: myenedis_import_statistics
description: Insert a long term statistic entry based on myenedis yesterday value. 
fields:
  history_sensor_name:
     description: Name of the history sensor containing statistics. Default=myenedis_statistics
     example: myenedis_statistics
     required: false
  myenedis_sensor_name:
     description: Name of the sensor containing myenedis attributes.
     example: sensor.myenedis_xxxxxxx
     required: true
  domain_name:
     description: Domain name of the sensor. The sensor will be <domain_name>:<history_sensor_name>
     example: myenedis
     required: false
"""    
    # Hassio task name
    task.unique("myenedis_import_statistics")

    # HomeAssistant global  hass
    global hass

    # parameters ?
    _LOGGER.info(f"history_sensor_name={history_sensor_name}, myenedis_sensor_name={myenedis_sensor_name}, domain_name={domain_name}")

    # defines what attribute and unit to use - based on parameters
    statistics_unit = UnitOfEnergy.KILO_WATT_HOUR
    _LOGGER.info(f"Attribute used statistics_unit={statistics_unit} ")

    # defines staittics name (sensor name)
    statistic_id = f"{domain_name}:{history_sensor_name}".lower()

    # search for the latest statistics (date & last sum)
    last_stats = await homeassistant.components.recorder.get_instance(hass).async_add_executor_job(
        get_last_statistics, hass, 1, statistic_id, True, {'state','sum'})

    # default value if no match
    last_sum = 0
    last_date = datetime.datetime(year=1900, month=1, day=1,hour=0, minute=0, second=0, microsecond=0, tzinfo=datetime.timezone.utc)

    # do we have match (existing stats ?)
    if (last_stats is not None):
        if (len(last_stats) != 0):
            last_sum = last_stats[statistic_id][0]['sum']
            if (last_sum is not None):
                last_sum = int(last_sum)
                last_date = last_stats[statistic_id][0]['start']

    _LOGGER.info(f"LAST SUM={last_sum} LAST_DATE={last_date} ")
    _LOGGER.info(f"------------------------")

    # 

    statistics = []

    dailyweek = get_attribute(f'{myenedis_sensor_name}.dailyweek')
    dailyweek_HC = get_attribute(f'{myenedis_sensor_name}.dailyweek_HC')
    dailyweek_HP = get_attribute(f'{myenedis_sensor_name}.dailyweek_HP')
    if (dailyweek is None) or (dailyweek_HC is None)  or (dailyweek_HP is None):
        _LOGGER.error("attribute not found. Job ended.")
        return

    for i in range(len(dailyweek),0, -1):
        decal = i -1
        i_year=int(dailyweek[i-1][0:4]) ;  i_month=int(dailyweek[i-1][5:7]) ;   i_day=int(dailyweek[i-1][8:10])
        dt = datetime.datetime(year=i_year, month=i_month,day=i_day,hour=0, minute=0, second=0, microsecond=0, tzinfo=datetime.timezone.utc)

        new_state = float(dailyweek_HP[i-1]) + float(dailyweek_HC[i-1]) 

        if (new_state <0 -1 ):
            _LOGGER.warning(f"Value not avialable to this date {dt} val={new_state} ")
            break

        if (dt > last_date):
            # state & sum
            last_sum += new_state
            new_sum = last_sum

            _LOGGER.info(f"Daily Date={dt} Delta={new_state} sum={new_sum} ")
            # add to list
            statistics.append(StatisticData(start=dt, state=new_state, sum=new_sum))
        else:
            _LOGGER.info(f"Date skipped {dt}. already have statistics. ")

    # prepare list of stat to be inserted
    metadata = StatisticMetaData(has_mean=False, has_sum=True, 
                name=history_sensor_name,
                source=domain_name,
                statistic_id=statistic_id,
                unit_of_measurement=statistics_unit )


    # if we have stat to insert... go
    if (len(statistics)>0):       
        _LOGGER.info(f"adding {len(statistics)} statistics for column {statistic_id}")
        async_add_external_statistics(hass , metadata, statistics)

    _LOGGER.info(f"--------THE---END-------")

