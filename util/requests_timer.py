""" Helper functions for HTTP requests. """
import random
import time


def delay_next_request() -> None:
    # reduce request frequency to prevent getting blocked
    time.sleep(random.choice(list(range(60, 65))))