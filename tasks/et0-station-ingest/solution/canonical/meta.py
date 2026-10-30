"""Station register: read the stations YAML into Station records (fields are described in /app/docs/METHOD.md)."""
from dataclasses import dataclass

import yaml


@dataclass(frozen=True)
class Station:
    station_id: str
    name: str
    latitude: float          # decimal degrees, north positive
    longitude: float
    elevation_m: float
    wind_height_m: float
    radiation_units: str
    humidity: str
    network: str


def parse_latitude(value):
    """Latitude in decimal degrees.

    The register holds plain numbers (38.42, -31.85) and, for stations imported from the synop and coast networks,
    text with a hemisphere letter ("36.95N").
    """
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().upper()
    if text.endswith("S"):
        return -abs(float(text[:-1]))
    if text.endswith("N"):
        return abs(float(text[:-1]))
    return float(text)


def load_stations(path):
    with open(path, encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    stations = []
    for rec in doc["stations"]:
        stations.append(Station(
            station_id=str(rec["id"]),
            name=str(rec.get("name", "")),
            latitude=parse_latitude(rec["latitude"]),
            longitude=float(rec["longitude"]),
            elevation_m=float(rec["elevation_m"]),
            wind_height_m=float(rec["wind_height_m"]),
            radiation_units=str(rec["radiation_units"]),
            humidity=str(rec["humidity"]),
            network=str(rec.get("network", "")),
        ))
    return stations
