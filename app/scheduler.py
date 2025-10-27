from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from .harvest import Runner
from .settings import settings

def _cron_triggers():
    triggers = []
    for expr in settings.SCHEDULE_CRONS:
        expr = (expr or "").strip()
        if not expr:
            continue
        try:
            triggers.append(CronTrigger.from_crontab(expr, timezone=settings.TZ))
        except ValueError:
            continue
    if not triggers:
        triggers.append(CronTrigger(hour=7, minute=40, timezone=settings.TZ))
    return triggers

_sched = None
_runner = Runner()

def start_scheduler():
    global _sched
    if _sched:
        return _sched
    _sched = BackgroundScheduler(timezone=settings.TZ)
    for trig in _cron_triggers():
        _sched.add_job(_runner.run_once, trig)
    _sched.start()
    return _sched
