import random
import zoneinfo
import requests
from typing import Dict, Any

from plugins.base import BasePlugin
from django.template.loader import get_template
from django.utils import timezone
from django.utils.dateparse import parse_datetime


class IdfmMetroPlugin(BasePlugin):
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

    def api_key(self):
        if not self.config.get("api_key"):
            raise ValueError("API key not set")
        return self.config["api_key"]

    def lines(self):
        if not self.config.get("lines"):
            raise ValueError("Lines not set")
        return self.config["lines"]

    def timezone(self):
        return self.config.get("timezone", "Europe/Paris")

    def generate_html(self):
        template = get_template("idfm_metro/full.html")
        html = template.render({"lines": self.get_data()})
        return html

    def fetch_stop_monitoring(self, stop_id):
        next_stops = []
        response = requests.get(
            "https://prim.iledefrance-mobilites.fr/marketplace/stop-monitoring",
            params={"MonitoringRef": f"STIF:StopPoint:Q:{stop_id}:"},
            headers={"apikey": self.api_key()},
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
        timezone.activate(zoneinfo.ZoneInfo(self.timezone()))
        data = []
        for line in self.lines():
            line_data = {"name": line["name"], "code": line["code"], "next_stops": []}
            stop_id = line.get("stop_id", "")
            stop_data = self.fetch_stop_monitoring(stop_id)
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

    # @classmethod
    # def fetch_random_pokemon(cls) -> Dict[str, Any]:
    #     """Fetch random Pokemon data from PokeAPI."""
    #     pokemon_id = random.randint(1, cls.__MAX_POKEMON_ID)
    #     response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}")
    #     pokemon_data = response.json()

    #     types = [t["type"]["name"] for t in pokemon_data["types"]]
    #     abilities = [a["ability"]["name"] for a in pokemon_data["abilities"]]

    #     species_url = pokemon_data["species"]["url"]
    #     species_response = requests.get(species_url)
    #     species_data = species_response.json()

    #     for genus in species_data["genera"]:
    #         if genus["language"]["name"] == "en":
    #             species_name = genus["genus"]
    #             break
    #     else:
    #         species_name = species_data["name"]

    #     return {
    #         "name": pokemon_data["name"].title(),
    #         "types": ", ".join(type.title() for type in types),
    #         "species": species_name.title(),
    #         "height": f"{pokemon_data["height"] / 10} m",  # Convert to meters
    #         "weight": f"{pokemon_data["weight"] / 10} kg",  # Convert to kilograms
    #         "abilities": ", ".join(ability.title() for ability in abilities),
    #         "artwork": pokemon_data["sprites"]["other"]["official-artwork"]["front_default"]
    #     }
