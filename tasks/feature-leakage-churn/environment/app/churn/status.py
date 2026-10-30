"""Account status from the billing system's status snapshots."""


def latest_status(points, snapshots):
    """Status of the customer's latest snapshot."""
    latest = (snapshots.sort_values(["customer_id", "snapshot_date"])
              .drop_duplicates("customer_id", keep="last"))
    return points[["customer_id"]].merge(latest[["customer_id", "status"]], on="customer_id", how="left")["status"]
