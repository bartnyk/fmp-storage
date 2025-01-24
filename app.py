import asyncio

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from cli import get_latest_forex_data, get_latest_forex_events

scheduler = BackgroundScheduler()
trigger = IntervalTrigger(minutes=10)


if __name__ == "__main__":
    scheduler.add_job(lambda: asyncio.run(get_latest_forex_data()), trigger, max_instances=1, replace_existing=True)
    scheduler.add_job(
        lambda: asyncio.run(get_latest_forex_events(gui=False)), trigger, max_instances=1, replace_existing=True
    )
    scheduler.start()
    try:
        while True:
            ...
    except:
        scheduler.shutdown()
