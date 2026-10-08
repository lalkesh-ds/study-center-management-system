from datetime import date, time


def time_to_minutes(t: time) -> int:
    """
    Converts datetime.time into minutes from midnight (0 to 1440).
    E.g. 07:00:00 -> 420, 11:00:00 -> 660, 23:00:00 -> 1380.
    """
    return t.hour * 60 + t.minute


def minutes_to_time(minutes: int) -> time:
    """
    Converts minutes from midnight back into datetime.time.
    """
    hour = (minutes // 60) % 24
    minute = minutes % 60
    return time(hour, minute, 0)


def intervals_overlap(start1: int, end1: int, start2: int, end2: int) -> bool:
    """
    Pure mathematical overlap evaluation for half-open intervals [S1, E1) and [S2, E2).
    Two half-open intervals collide if and only if:
        max(S1, S2) < min(E1, E2)  <=>  S1 < E2 and S2 < E1
    Touching boundaries (e.g. 11:00 end and 11:00 start) return False (NO collision).
    """
    return start1 < end2 and start2 < end1


def date_ranges_overlap(start1: date, end1: date, start2: date, end2: date) -> bool:
    """
    Pure mathematical overlap evaluation for inclusive calendar date ranges [D1_start, D1_end] and [D2_start, D2_end].
    Two inclusive calendar spans collide if and only if:
        D1_start <= D2_end and D2_start <= D1_end
    Consecutive months (e.g. Oct 1-31 vs Nov 1-30) return False (NO collision).
    """
    return start1 <= end2 and start2 <= end1
