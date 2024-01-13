################### TIME ###################

SECONDS_PER_MINUTE = 60
MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24
SECONDS_PER_HOUR = SECONDS_PER_MINUTE * MINUTES_PER_HOUR
SECONDS_PER_DAY = SECONDS_PER_HOUR * HOURS_PER_DAY
MINUTES_PER_DAY = HOURS_PER_DAY * MINUTES_PER_HOUR

def minutes(start_time:float, end_time:float) -> float:
    dseconds = end_time - start_time
    return dseconds / SECONDS_PER_MINUTE

def hours(start_time:float, end_time:float) -> float:
    dminutes = minutes(start_time, end_time)
    return dminutes / MINUTES_PER_HOUR

def days(start_time:float, end_time:float) -> float:
    dhours = hours(start_time, end_time)
    return dhours / HOURS_PER_DAY
