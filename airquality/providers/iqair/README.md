# IQAir Data Provider

A proprietary plugin providing data retrieval from IQAir API.

# Polling Rules

Interval: 1h

Limit per minute: 5
Limit per day: 500
Limit per month: 10000

# Reference

## Configuration

```json
{
    "api_key": "str",
    "target_polling_interval": 3600,
    "targets": [
        {
            "city": "Belgrade",
            "state": "Central Serbia",
            "country": "Serbia",
        },
        {
            "city": "Stockholm",
            "state": "Stockholm",
            "country": "Sweden",
        },

    ]
}
```

## Example dataset

```json
{
    "status": "success",
    "data": {
        "city": "Belgrade",
        "state": "Central Serbia",
        "country": "Serbia",
        "location": {
            "type": "Point",
            "coordinates": [
                20.459113,
                44.82112
            ]
        },
        "current": {
            "pollution": {
                "ts": "2025-02-07T07:00:00.000Z",
                "aqius": 77,
                "mainus": "p2",
                "aqicn": 33,
                "maincn": "p2"
            },
            "weather": {
                "ts": "2025-02-07T07:00:00.000Z",
                "tp": 0,
                "pr": 1037,
                "hu": 66,
                "ws": 4.63,
                "wd": 120,
                "ic": "13d"
            }
        }
    }
}
```

## Parameters

* "aqius": AQI value based on US EPA standard
* "aqicn": AQI value based on China MEP standard
* "tp": temperature in Celsius
* "pr": atmospheric pressure in hPa
* "hu": humidity %
* "ws": wind speed (m/s)
* "wd": wind direction, as an angle of 360° (N=0, E=90, S=180, W=270)
* "ic": weather icon code, see below for icon index

## Interpretation of AQI

Air agencies across the U.S. use the Air Quality Index (AQI) to communicate about air quality.

* Good: 0-50
* Moderate: 51-100
* Unhealthy for sensitive groups: 101-150
* Unhealthy: 151-200
* Very unhealthy: 201-300
* Hazadrous: 301+

# TODO

* Handle unexpected "too many requests"
* Count errors

