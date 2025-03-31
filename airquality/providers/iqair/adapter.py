#!/usr/bin/env python3
# pylint: disable=line-too-long, missing-function-docstring, logging-fstring-interpolation
# pylint: disable=too-many-locals, broad-except, too-many-arguments, raise-missing-from
# pylint: disable=import-error,f-string-without-interpolation
"""

  IQAir API Adapter

"""

import threading
import logging
import datetime
import time
from urllib.parse import urljoin

import requests

from pyp8s import MetricsHandler
from .exceptions import (
    UsageLimitsHitException,
    APIResponseFailedException,
)


logger = logging.getLogger(__name__)


def retry(attempts=10, delay=None):

    def decorate(func):
        def wrap(*args, **kwargs):

            current_attempt = 0

            while True:
                current_attempt += 1
                logger.debug(f"Retry #{current_attempt} for function: {func}")

                try:
                    result = func(*args, **kwargs)
                    return result

                except Exception as e:
                    logger.error(f"Retry #{current_attempt} for function: {func} failed: {e}")

                    if attempts is not None:
                        if current_attempt >= attempts:
                            raise e

                    if delay is not None:
                        time.sleep(delay)

        return wrap

    return decorate


class Adapter(threading.Thread):
    """
    Data provider thread class
    """

    def __init__(self, adapter_config, thread_name=None):
        super().__init__()

        self.api_key = None
        self.api_base_url = None
        self.api_version = None
        self.api_query_limit_minute = None
        self.api_query_limit_day = None
        self.api_query_limit_month = None

        self.targets = None
        self.target_polling_interval = None
        self.target_polling_backoff_threshold = 120

        self.daemon = False
        self.alive = True

        self._parse_configuration(**adapter_config)
        self._initialise_metrics()

        self.api_query_usage = {
            "total_requests": 0,
            "minute": {
                "threshold": self.api_query_limit_minute,
                "timestamp": datetime.datetime.now(),
            },
            "day": {
                "threshold": self.api_query_limit_day,
                "timestamp": datetime.datetime.now(),
            },
            "month": {
                "threshold": self.api_query_limit_month,
                "timestamp": datetime.datetime.now(),
            },
        }

        if thread_name is None:
            self.name = "IQAirAdapter"
        else:
            self.name = thread_name

    def _check_limit_minute(self):
        logger.debug(f"Minute usage limit validation started")
        now = datetime.datetime.now().replace(microsecond=0)

        minute_count_reached = self.api_query_usage['total_requests'] >= self.api_query_usage["minute"]["threshold"]
        logger.debug(f"Minute usage limit reached by request count: {minute_count_reached}")

        minute_time_last = self.api_query_usage["minute"]["timestamp"].replace(microsecond=0, second=0)
        minute_time_now = now.replace(microsecond=0, second=0)
        minute_time_expired = minute_time_now > minute_time_last
        logger.debug(f"Minute usage limit expired: {minute_time_expired}")

        if minute_count_reached and not minute_time_expired:
            logger.warning(f"IQAir API request limit reached per minute: {self.api_query_usage['total_requests']} vs {self.api_query_usage['minute']['threshold']}")

            next_minute = (minute_time_last + datetime.timedelta(minutes=1)).replace(microsecond=0)
            logger.debug(f"Now: {now}")
            logger.debug(f"Last usage timestamp: {self.api_query_usage['minute']['timestamp']}")
            logger.debug(f"Next minute calculated: {next_minute}")
            logger.debug(f"Delta calculated: {(next_minute - now)}")

            backoff_seconds = (next_minute - now).seconds
            logger.warning(f"IQAir API request backoff: {backoff_seconds} sec.")

            return {"ok": False, "backoff": backoff_seconds}

        elif not minute_count_reached and not minute_time_expired:
            logger.debug(f"IQAir API request limit per minute not reached: {self.api_query_usage['total_requests']} vs {self.api_query_usage['minute']['threshold']}")
            return {"ok": True}

        elif minute_time_expired:
            logger.debug(f"IQAir API request limits per minute expired: resetting the threshold, and the timestamp")
            self.api_query_usage["minute"]["threshold"] = self.api_query_usage["total_requests"] + self.api_query_limit_minute
            self.api_query_usage["minute"]["timestamp"] = datetime.datetime.now()
            return {"ok": True}

    def _check_limit_day(self):
        logger.debug(f"Day usage limit validation started")
        now = datetime.datetime.now()

        day_count_reached = self.api_query_usage['total_requests'] >= self.api_query_usage["day"]["threshold"]
        logger.debug(f"Day usage limit reached by request count: {day_count_reached}")

        day_time_last = self.api_query_usage["day"]["timestamp"].date()
        day_time_now = now.date()
        day_time_expired = day_time_now > day_time_last
        logger.debug(f"Day usage limit expired: {day_time_expired}")

        if day_count_reached and not day_time_expired:
            logger.warning(f"IQAir API request limit reached per day: {self.api_query_usage['total_requests']} vs {self.api_query_usage['day']['threshold']}")

            next_day = day_time_last + datetime.timedelta(days=1)
            logger.debug(f"Now: {now}")
            logger.debug(f"Last usage timestamp: {self.api_query_usage['day']['timestamp']}")
            logger.debug(f"Next day calculated: {next_day}")
            logger.debug(f"Delta calculated: {(next_day - now)}")

            backoff_seconds = (next_day - now).seconds
            logger.warning(f"IQAir API request backoff: {backoff_seconds} sec.")

            return {"ok": False, "backoff": backoff_seconds}

        elif not day_count_reached and not day_time_expired:
            logger.debug(f"IQAir API request limit per day not reached: {self.api_query_usage['total_requests']} vs {self.api_query_usage['day']['threshold']}")
            return {"ok": True}

        elif day_time_expired:
            logger.debug(f"IQAir API request limits per day expired: resetting the threshold, and the timestamp")
            self.api_query_usage["day"]["threshold"] = self.api_query_usage["total_requests"] + self.api_query_limit_day
            self.api_query_usage["day"]["timestamp"] = datetime.datetime.now()
            return {"ok": True}

    def _check_limits(self):
        logger.debug(f"Checking IQAir API usage limits")

        day_limit = self._check_limit_day()

        if not day_limit['ok']:
            logger.warning(f"IQAir API usage hit the daily limits, backoff time {day_limit['backoff']} sec")
            raise UsageLimitsHitException(f"IQAir API usage hit the daily limits", day_limit['backoff'])

        minute_limit = self._check_limit_minute()

        if not minute_limit['ok']:
            logger.warning(f"IQAir API usage hit the minute limits, backoff time {minute_limit['backoff']} sec")
            raise UsageLimitsHitException(f"IQAir API usage hit the minute limits", minute_limit['backoff'])

        logger.debug(f"IQAir API usage limits are OK")
        return True

    def _parse_configuration(self, api_key, *args,
                             api_base_url="https://api.airvisual.com/", api_version="v2",
                             api_query_limit_minute=5, api_query_limit_day=500, api_query_limit_month=10000,
                             targets=None, target_polling_interval=60*60,
                             **kwargs):
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.api_version = api_version
        self.api_query_limit_minute = api_query_limit_minute
        self.api_query_limit_day = api_query_limit_day
        self.api_query_limit_month = api_query_limit_month

        self.target_polling_interval = target_polling_interval

        if targets is not None:
            self.targets = targets
        else:
            self.targets = []

        if args:
            logger.warning(f"Ignored configuration parameters: {args}")

        if kwargs:
            logger.warning(f"Ignored configuration parameters: {kwargs}")

    def _initialise_metrics(self):
        MetricsHandler.init("airquality_iqair_target_results", "counter", "IQAir Adapter plugin, target fetching results")
        MetricsHandler.init("airquality_iqair_usage_requests_total", "counter", "IQAir Adapter plugin, total API requests")
        MetricsHandler.init("airquality_iqair_backoff_time_total", "counter", "IQAir Adapter plugin, total backoff time")
        MetricsHandler.init("airquality_iqair_errors", "counter", "IQAir Adapter plugin errors")

    def _extract_time_from_ts(self, ts):
        try:
            weather_update_time_str = ts.split(".")[0]
            weather_update_time = datetime.datetime.fromisoformat(weather_update_time_str)
            return int(weather_update_time.timestamp())

        except Exception as e:
            logger.error(f"Couldn't extract time from {ts} ({e.__class__.__name__}): {e}")
            logger.warning(f"Falling back to local time as update timestamp")
            return int(time.time())

    def _update_metrics(self, data, labels):
        pollution = data["current"]["pollution"]
        weather = data["current"]["weather"]

        MetricsHandler.set("airquality_aqius",          pollution["aqius"], **labels)
        MetricsHandler.set("airquality_aqicn",          pollution["aqicn"], **labels)
        MetricsHandler.set("airquality_temperature",    weather["tp"],      **labels)
        MetricsHandler.set("airquality_pressure_hpa",   weather["pr"],      **labels)
        MetricsHandler.set("airquality_humidity",       weather["hu"],      **labels)
        MetricsHandler.set("airquality_wind_speed",     weather["ws"],      **labels)
        MetricsHandler.set("airquality_wind_direction", weather["wd"],      **labels)

        weather_update_time = self._extract_time_from_ts(weather['ts'])
        MetricsHandler.set("airquality_last_update", weather_update_time, subject="weather", **labels)

        pollution_update_time = self._extract_time_from_ts(pollution['ts'])
        MetricsHandler.set("airquality_last_update", pollution_update_time, subject="pollution", **labels)

        return True

    @retry(attempts=10)
    def _retrieve_data(self, country, state, city):
        try:
            self._check_limits()

            versioned_url = urljoin(f"{self.api_base_url}/", f"/{self.api_version}/")
            logger.debug(f"IQAir API versioned URL: {versioned_url}")

            url = urljoin(versioned_url, "city")
            logger.debug(f"IQAir API URL: {url}")

            params = {
                "city": city,
                "state": state,
                "country": country,
                "key": self.api_key,
            }
            logger.debug(f"IQAir API request parameters: {params}")

            headers = {}

            response = requests.request("GET", url, headers=headers, params=params)
            logger.debug(f"IQAir API response: status_code={response.status_code}")
            logger.debug(f"IQAir API response: text={response.text}")

            self.api_query_usage['total_requests'] += 1
            MetricsHandler.inc("airquality_iqair_usage_requests_total", 1)
            logger.debug(f"IQAir API usage incremented total requests counter: {self.api_query_usage['total_requests']}")

            if response.status_code == 429:
                logger.error(f"IQAir API returned 429 Too many requests, total_requests={self.api_query_usage['total_requests']}, threshold={self.api_query_usage['minute']['threshold']}")
                raise UsageLimitsHitException(f"IQAir API returned 429 Too many requests", 60)

            elif response.status_code == 200:

                response_json = response.json()
                logger.debug(f"IQAir API response: json={response_json}")

                if response_json['status'] != 'success':
                    raise APIResponseFailedException(f"IQAir API didn't return with a success: {response_json}")

                labels = {
                    "provider": "IQAir",
                    "city": city,
                    "state": state,
                    "country": country,
                }

                metrics_update_result = self._update_metrics(data=response_json['data'], labels=labels)
                return metrics_update_result

            else:
                raise APIResponseFailedException(f"IQAir API request failed: status_code={response.status_code} text={response.text}")

        except UsageLimitsHitException as e:
            logger.error(f"Interrupting polling cycle for country={country}, state={state}, city={city} because of the IQAir API usage limits")
            MetricsHandler.inc("airquality_iqair_errors", 1, area="retrieve_data", reason="limit")

            if e.backoff_seconds:
                if e.backoff_seconds < self.target_polling_backoff_threshold:
                    logger.warning(f"Waiting for the backoff time of {e.backoff_seconds} sec to pass before retrying")
                    time.sleep(e.backoff_seconds)
                    MetricsHandler.inc("airquality_iqair_backoff_time_total", e.backoff_seconds)
            raise e

        except APIResponseFailedException as e:
            logger.error(f"Interrupting polling cycle for country={country}, state={state}, city={city} because of an API interaction error: {e}")
            MetricsHandler.inc("airquality_iqair_errors", 1, area="retrieve_data", reason="api_error")
            return False

        except Exception as e:
            logger.exception(f"Couldn't retrieve data for country={country}, state={state}, city={city} from IQAir API {e.__class__.__name__}: {e}")
            MetricsHandler.inc("airquality_iqair_errors", 1, area="retrieve_data", reason="unhandled")
            raise e

    def run(self):
        while self.alive:
            for target in self.targets:
                retrieve_data_result = self._retrieve_data(**target)
                MetricsHandler.inc("airquality_iqair_target_results", 1, outcome=retrieve_data_result, **target)

            logger.debug(f"Sleeping for {self.target_polling_interval} sec until the next polling cycle")
            time.sleep(self.target_polling_interval)

    def stop(self):
        logger.warning(f"Stoppting the thread: {self.name}")
        self.alive = False
