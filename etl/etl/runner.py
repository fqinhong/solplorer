import logging
import sys

from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.schedulers.blocking import BlockingScheduler

from .jobs.dau import update_dau
from .jobs.dtxfees import update_dtxfees
from .jobs.epoch import update_epoch
from .jobs.markets import update_markets
from .jobs.news import update_news
from .jobs.nft_collections import update_nft_collections
from .jobs.stats import update_stats
from .jobs.supply import update_supply
from .jobs.tokens_cmc import update_tokens
from .jobs.top10 import update_top10
from .jobs.tvl import update_tvl


class Runner:
    def __init__(self, loghandler=logging.StreamHandler(), loglevel=logging.WARN):
        self.logger = logging.getLogger("solplorer.etl.Runner")
        self.logger.setLevel(loglevel)

        self.scheduler = BlockingScheduler(
            {
                "apscheduler.timezone": "UTC",
                "apscheduler.job_defaults.max_instances": "2",
            }
        )
        ap_logger = logging.getLogger("apscheduler")
        ap_logger.handler = []
        ap_logger.setLevel(loglevel)
        ap_logger.addHandler(loghandler)

        self.scheduler.add_listener(self.handle_scheduler_error, EVENT_JOB_ERROR)

    @staticmethod
    def create(*args, **kwargs):
        return Runner(*args, **kwargs)

    def handle_scheduler_error(self, ev):
        self.logger.fatal("Unhandled job exception", ev.exception, ev.traceback)
        self.scheduler.shutdown(False)
        sys.exit(1)

    def run(self):
        self.scheduler.add_job(update_stats, "interval", seconds=15)
        self.scheduler.add_job(update_epoch, "cron", minutes="*/10")
        self.scheduler.add_job(update_markets, "cron", minute="*/15")
        self.scheduler.add_job(update_top10, "cron", minute=0)
        self.scheduler.add_job(update_news, "cron", minute=5)
        self.scheduler.add_job(update_tvl, "cron", minute=10)
        self.scheduler.add_job(update_tokens, "cron", hour=1, minute=0)
        self.scheduler.add_job(update_supply, "cron", hour=1, minute=5)
        self.scheduler.add_job(update_nft_collections, "cron", hour=1, minute=10)
        self.scheduler.add_job(update_dau, "cron", hour=12)
        self.scheduler.add_job(update_dtxfees, "cron", hour=12, minute=5)

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            self.logger.warn("Received exit signal, terminating.")
        except Exception as error:
            self.scheduler.shutdown(False)
            self.logger.fatal("Unhandled exception", error)
            sys.exit(1)
