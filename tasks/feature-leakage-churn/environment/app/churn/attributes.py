"""Customer attributes from the customer record (new in v3): the subscription plan and the days since the last login.

Point in time: a last login at or after the prediction time is ignored (the feature is null then), so the feature
never looks ahead of t.
"""


def plan(points, customers):
    """The customer's subscription plan."""
    return points["customer_id"].map(customers.set_index("customer_id")["plan"])


def days_since_last_login(points, customers):
    """t minus the customer's last login, in days; null when the record has no login before t."""
    last = points["customer_id"].map(customers.set_index("customer_id")["last_login_at"])
    days = (points["as_of"] - last).dt.total_seconds() / 86400
    return days.where(last < points["as_of"])
