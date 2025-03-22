import zoneinfo

import requests
from django.template.loader import get_template
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from plugins.recipe import BaseRecipe


class IdfmMetroRecipe(BaseRecipe):
    """
    config example:
    {
        "api_key": "your_api_key",
        "timezone": "Europe/Paris",
        "lines": [
          {
            "name": "Ligne 8",
            "code": "8",
            "stop_id": 123
          }
        ]
    }
    """

    @property
    def api_key(self):
        if not self.config.get("api_key"):
            raise ValueError("API key not set")
        return self.config["api_key"]

    @property
    def lines(self):
        if not self.config.get("lines"):
            raise ValueError("Lines not set")
        return self.config["lines"]

    @property
    def timezone(self):
        return self.config.get("timezone", "Europe/Paris")

    def generate_html(self):
        template = get_template("idfm_metro/full.html")
        return template.render({"lines": self.get_data()})

    def fetch_stop_monitoring(self, stop_id):
        next_stops = []
        response = requests.get(
            "https://prim.iledefrance-mobilites.fr/marketplace/stop-monitoring",
            params={"MonitoringRef": f"STIF:StopPoint:Q:{stop_id}:"},
            headers={"apikey": self.api_key},
        )
        monitored_stop_visit = response.json()["Siri"]["ServiceDelivery"][
            "StopMonitoringDelivery"
        ][0]["MonitoredStopVisit"]
        for stop in monitored_stop_visit:
            journey = stop["MonitoredVehicleJourney"]
            destination_name = journey["DirectionName"][0]["value"]
            stop_name = journey["MonitoredCall"]["StopPointName"][0]["value"]
            expected_arrival_time = journey["MonitoredCall"]["ExpectedArrivalTime"]
            status = journey["MonitoredCall"]["DepartureStatus"]
            next_stops += [
                {
                    "destination_name": destination_name,
                    "stop_name": stop_name,
                    "expected_arrival_time": expected_arrival_time,
                    "status": status,
                }
            ]
        return next_stops

    def get_data(self):
        timezone.activate(zoneinfo.ZoneInfo(self.timezone))
        data = []
        for line in self.lines:
            line_data = {"name": line["name"], "code": line["code"], "next_stops": []}
            stop_id = line.get("stop_id", "")
            stop_data = self.fetch_stop_monitoring(stop_id)
            if not stop_data:
                continue
            stop_name = stop_data[0]["stop_name"]
            destination_name = stop_data[0]["destination_name"]
            for stop in stop_data:
                del stop["stop_name"]
                del stop["destination_name"]
                local_datetime = timezone.localtime(
                    parse_datetime(stop["expected_arrival_time"])
                )
                stop["expected_arrival_time"] = local_datetime.strftime("%H:%M")
            line_data["next_stops"] = stop_data
            if "stop_name" not in line_data:
                line_data["stop_name"] = stop_name
            if "destination" not in line_data:
                line_data["destination"] = destination_name
            data += [line_data]
        return data
