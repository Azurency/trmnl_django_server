import random
from typing import Any, Dict

import requests
from django.template.loader import get_template

from plugins.recipe import BaseRecipe


class PokemonRecipe(BaseRecipe):
    """
    config example:
    {
        "lang": "fr",
    }
    """

    __MAX_POKEMON_ID = 1025

    @property
    def lang(self):
        return self.config.get("lang", "en")

    def generate_html(self):
        template = get_template("whos-that-pokemon/full.html")
        return template.render({"pokemon_data": self.fetch_random_pokemon()})

    def get_translated_pokemon_name(self, pokemon_name):
        url = f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_name.lower()}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            for name in data["names"]:
                if name["language"]["name"] == self.lang:
                    return name["name"]
        return ""

    def fetch_random_pokemon(self) -> Dict[str, Any]:
        """Fetch random Pokemon data from PokeAPI."""
        pokemon_id = random.randint(1, self.__MAX_POKEMON_ID)
        response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}")
        pokemon_data = response.json()

        types = [t["type"]["name"] for t in pokemon_data["types"]]
        abilities = [a["ability"]["name"] for a in pokemon_data["abilities"]]

        species_url = pokemon_data["species"]["url"]
        species_response = requests.get(species_url)
        species_data = species_response.json()

        species_name = next(
            (
                genus["genus"]
                for genus in species_data["genera"]
                if genus["language"]["name"] == self.lang
            ),
            species_data["name"],
        )
        return {
            "name": self.get_translated_pokemon_name(pokemon_data["name"]).title(),
            "types": ", ".join(type.title() for type in types),
            "species": species_name.title(),
            "height": f"{pokemon_data['height'] / 10} m",  # Convert to meters
            "weight": f"{pokemon_data['weight'] / 10} kg",  # Convert to kilograms
            "abilities": ", ".join(ability.title() for ability in abilities),
            "artwork": pokemon_data["sprites"]["other"]["official-artwork"][
                "front_default"
            ],
        }
