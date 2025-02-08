#!/usr/bin/env python3
# pylint: disable=line-too-long, missing-function-docstring, logging-fstring-interpolation
# pylint: disable=too-many-locals, broad-except, too-many-arguments, raise-missing-from
# pylint: disable=import-error
"""

  Air Quality Exporter
  ====================

  Provides air quality information.

  GitHub repository:
  https://github.com/pyp8s/airquality

  Community support:
  https://github.com/pyp8s/airquality/issues

  Copyright © 2025, Pavel Kim

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

from pyp8s import MetricsHandler

from providers import iqair

from configuration import (
    METRICS_LISTEN_ADDRESS,
    METRICS_LISTEN_PORT,
    PROVIDERS,
)


if __name__ == "__main__":

    MetricsHandler.init("airquality_aqius", "gauge", "AQI value based on US EPA standard")
    MetricsHandler.init("airquality_aqicn", "gauge", "AQI value based on China MEP standard")
    MetricsHandler.init("airquality_temperature", "gauge", "Temperature in Celsius")
    MetricsHandler.init("airquality_pressure_hpa", "gauge", "Atmospheric pressure in hPa")
    MetricsHandler.init("airquality_humidity", "gauge", "Humidity %")
    MetricsHandler.init("airquality_wind_speed", "gauge", "Wind speed (m/s)")
    MetricsHandler.init("airquality_wind_direction", "gauge", "Wind direction, as an angle of 360° (N=0, E=90, S=180, W=270)")

    MetricsHandler.serve(listen_address=METRICS_LISTEN_ADDRESS, listen_port=METRICS_LISTEN_PORT)

    provider = iqair.Adapter(adapter_config=PROVIDERS['iqair'])
    provider.run()
