"""Gap filling for upstream readings that arrive with holes (analytics export outages, devices offline).

Point in time (FEATURES.md, app_minutes_7d): a missing reading takes the customer's most recent earlier reading,
never a later one; with no earlier reading it stays null.
"""


def fill_app_minutes(points):
    """Fill missing app_minutes_7d from the same customer's last earlier reading."""
    pts = points.sort_values(["customer_id", "as_of"], kind="mergesort")
    filled = pts.groupby("customer_id")["app_minutes_7d"].ffill()
    return filled.reindex(points.index)
