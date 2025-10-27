from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from .harvest import Runner

_sched = None
_runner = Runner()

def start_scheduler():
    global _sched
    if _sched:
        return _sched
    _sched = BackgroundScheduler(timezone="America/Chicago")
    _sched.add_job(_runner.run_once, CronTrigger(hour=7, minute=40))
    _sched.start()
    return _sched
