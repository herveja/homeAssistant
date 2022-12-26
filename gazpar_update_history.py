import json
import sqlalchemy
import pkg_resources
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy import and_, func
from datetime import datetime, timedelta


#################
# Global values
#################

GAZPAR_SENSOR_NAME = 'sensor.gazpar'
STATISTICS_SENSOR_NAME = 'sensor.gas_volume'

#################
# Helper classes
#################

class LOG_LEVEL():
    info = 1
    warning = 2
    error = 3
    debug = 4


class UPDATE_MODE():
    fixedDate = 1
    clearNewer = 2


class MaxFromPreviousDays:
    maxSum = 0
    maxState = 0

    def __init__(self, maxSum, maxState):
        self.maxSum = maxSum
        self.maxState = maxState


def print_log(msg, level=LOG_LEVEL.info):
    try:
        if level == LOG_LEVEL.info:
            log.info(msg)
        elif level == LOG_LEVEL.warning:
            log.warning(msg)
        elif level == LOG_LEVEL.error:
            log.error(msg)
        elif level == LOG_LEVEL.debug:
            log.debug(msg)
        else:
            log.warning("unmanaged log level for next message....")
            log.warning(msg)
    except NameError:
        print(msg)

#################
# etMetadataID
#################


def getMetadataID(session, sensorName):

    print_log("search for metadata_id",LOG_LEVEL.debug)
    
    res = session.query(StatisticsMeta).filter_by(statistic_id=sensorName)
    
    if res.count() < 1:
        print_log(f"{sensorName} not found in table Statistics.", LOG_LEVEL.error)
        return
    
    return res[0].id


def getMaxSum(metadataID, dt):

    sql = f"SELECT max(sum) as maxSum, max(state) as maxState  FROM statistics where metadata_id ={metadataID} and STRFTIME('%Y/%m/%d', start) < '{dt}' "
    
    rs = engine.execute(sql)
    
    maxSum = 0 ; maxState = 0
    
    for row in rs:
        if (row.maxSum is not None):
            maxSum = row.maxSum
            maxState = row.maxState
    
    print_log(f"Sum for {dt} is {maxSum} {maxState} ", LOG_LEVEL.debug)
    
    return MaxFromPreviousDays(maxSum, maxState)


def update_statistics(updateMode, metadataID, dt, previsousMaxs: MaxFromPreviousDays, newState):

    newSum = newState - previsousMaxs.maxState + previsousMaxs.maxSum

    print_log("Update mode={} id={} date={} prevSum={} prevState={}  newState={} newSum={} ".format(
        updateMode, metadataID, dt, previsousMaxs.maxSum, previsousMaxs.maxState, newState, newSum))

    signe = ">"
    if (updateMode == UPDATE_MODE.fixedDate):
        signe = "="

    sql = f"update statistics set sum={newSum}, state={newState} where metadata_id ={metadataID} and STRFTIME('%Y/%m/%d', start) {signe} '{dt}' "

    print_log(sql, LOG_LEVEL.debug)

    with engine.connect() as connection:
        with connection.begin():
            connection.execute(sql)


def init_bd_connection():
    global engine, State, Statistics, StatisticsMeta,  StateAttributes

    print_log("initializing sql objects", LOG_LEVEL.debug)

    engine = create_engine('sqlite:///./home-assistant_v2.db', echo=False)

    Base = automap_base()
    Base.prepare(engine, reflect=True)

    State = Base.classes.states
    Statistics = Base.classes.statistics
    StatisticsMeta = Base.classes.statistics_meta
    StateAttributes = Base.classes.state_attributes

@service
def gazpar_update_history(gazpar_sensor_name=None, statistics_sensor_name=None):

    # Hassio task name
    task.unique("gazpar_update_history")
    # check parameters
    if (gazpar_sensor_name is not None):
        gazparSensorName = gazpar_sensor_name
    else:
        gazparSensorName = GAZPAR_SENSOR_NAME
    if (statistics_sensor_name is not None):
        statisticsSensorName = statistics_sensor_name
    else:
        statisticsSensorName = STATISTICS_SENSOR_NAME
    print_log(f"Param used: Gazpar Sensor={gazparSensorName}, Statistics Sensor={statisticsSensorName}",LOG_LEVEL.info)
    # Create bd engine
    init_bd_connection()

    #Get attributes_id
    session = Session(engine)
    metadataID = getMetadataID(session, statisticsSensorName)
    if (metadataID is None):
        print_log("metadata ID not found. Job ended.", LOG_LEVEL.error)
        return

    print_log(f"metadata ID = {metadataID}", LOG_LEVEL.debug)

    res = session.query(State).filter_by(entity_id=gazparSensorName).order_by(State.last_updated.desc())
    if res.count() < 1:
        print_log(f"{gazparSensorName} not found in state table State. Job ended.", LOG_LEVEL.error)
        return
    attributesId = res[0].attributes_id

    # Get full attributes
    print_log(f"gazpar attributes_Id={attributesId}", LOG_LEVEL.debug)

    res = session.query(StateAttributes).filter_by(attributes_id=attributesId)
    if res.count() < 1:
        print_log(f"{attributesId} not found in state table state_attributes. job ended.", LOG_LEVEL.error)
        return

    # Transform gazpar attribute to JSON
    sharedAttrs = json.loads(res[0].shared_attrs)
    
    # Sort time_period desc
    sorted_list = sorted(sharedAttrs["daily"], key=lambda t: datetime.strptime(
        t['time_period'], '%d/%m/%Y'))
    dtTimePeriod = ""
    
    # Update statistics by date
    for d in sorted_list:
        dtTimePeriod = d["time_period"]
        dtsplit = dtTimePeriod.split('/')
        dtTimePeriod = f"{dtsplit[2]}/{dtsplit[1]}/{dtsplit[0]}"
        # Get sum before time_period
        maxs = getMaxSum(metadataID, dtTimePeriod)
        # Calculate new sum
        delta = d["end_index_m3"] - d["start_index_m3"]
        # Update
        update_statistics(UPDATE_MODE.fixedDate, metadataID, dtTimePeriod, maxs, d["end_index_m3"])
    
    # Clear history after the latest date
    if (dtTimePeriod != ""):
        update_statistics(UPDATE_MODE.clearNewer, metadataID, dtTimePeriod, maxs, d["end_index_m3"])


if __name__ == "__main__":
    print_log("Gazpar update history -- Starting")
    gazpar_update_history()
