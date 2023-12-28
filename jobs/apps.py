from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class JobsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobs'

    def ready(self):
        logger.info("JobConfig ready")
        from jobs.singal_processor import post_save_callback, post_delete_callback
