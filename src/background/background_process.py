from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta


class BackgroundProcess:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

    def debounce_run(self, job_id, function, second_after=1, **kwargs):
        print("add debounce run")
        if self.scheduler.get_job(job_id):
            print(f"{job_id} exist")
            self.scheduler.remove_job(job_id)

        run_date = datetime.now() + timedelta(seconds=second_after)
        # add jobs for run
        self.scheduler.add_job(
            function,
            'date',
            id=job_id,
            run_date=run_date,
            kwargs=kwargs
        )

    def interval_run(self, function, job_id=None, timeout_minute=1):
        if job_id and self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        self.scheduler.add_job(
            function,
            'interval',
            minutes=timeout_minute,
            id=job_id
        )
