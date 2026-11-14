from datetime import datetime

def current_datetime():
    now = datetime.now().astimezone()
    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "weekday": now.strftime("%A"),
        "timezone": now.tzname() or "Local",
        "iso": now.isoformat(timespec="seconds"),
    }
