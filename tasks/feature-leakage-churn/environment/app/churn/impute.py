"""Gap filling for upstream readings that arrive with holes (analytics export outages, devices offline)."""


def fill_app_minutes(points):
    """Fill missing app_minutes_7d from the nearest reading of the same customer."""
    pts = points.sort_values(["customer_id", "as_of"])
    filled = pts.groupby("customer_id")["app_minutes_7d"].transform(lambda s: s.bfill().ffill())
    return filled.reindex(points.index)
