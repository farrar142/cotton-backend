import os
import threading

from django.utils import autoreload

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def add_arguments(self, parser):
        parser.add_argument("tests", nargs="+", type=str)

    def handle(self, tests=[], *args, **options):
        def say():
            for test in tests:
                os.system(f"sh dev.sh test {test}")

        def run():
            thread = threading.Thread(target=say)
            thread.start()
            thread.join()
            print("end")

        autoreload.run_with_reloader(run)
