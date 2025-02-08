#!/usr/bin/env python3
# pylint: disable=line-too-long, missing-function-docstring, logging-fstring-interpolation
# pylint: disable=too-many-locals, broad-except, too-many-arguments, raise-missing-from
# pylint: disable=import-error,unnecessary-pass
"""

  IQAir API Adapter
  Exceptions

"""


class UsageLimitsHitException(Exception):
    """
    Raised when API usage limits were hit
    """
    def __init__(self, message, backoff_seconds=None):
        self.message = message
        self.backoff_seconds = backoff_seconds

        if self.backoff_seconds is not None:
            self.backoff_suffix = f"(backoff {self.backoff_seconds}sec)"
        else:
            self.backoff_suffix = ""

    def __str__(self):
        return " ".join([self.message, self.backoff_suffix, ])


class APIResponseFailedException(Exception):
    """
    Raised when API interaction has failed
    """
    pass
