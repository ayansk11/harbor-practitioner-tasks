"""Activity features over trailing windows (orders, spend, tickets) and simple time-since features."""
import numpy as np
import pandas as pd


def _daily(points, events, ts_col, amount_col=None):
    """Per customer and UTC day: number of events (and amount). Days that have a prediction but no event get 0."""
    ev = events.assign(day=events[ts_col].dt.floor("D"))
    agg = {"n": (ts_col, "size")}
    if amount_col:
        agg["amount"] = (amount_col, "sum")
    per_day = ev.groupby(["customer_id", "day"]).agg(**agg).reset_index()
    pred_days = points[["customer_id"]].assign(day=points["as_of"].dt.floor("D")).drop_duplicates()
    grid = pd.concat([per_day[["customer_id", "day"]], pred_days]).drop_duplicates()
    daily = grid.merge(per_day, on=["customer_id", "day"], how="left").fillna(0)
    return daily.sort_values(["customer_id", "day"]).reset_index(drop=True)


def _rolling(daily, cols, window):
    # daily buckets keep this fast; the window covers the last `window` including the prediction day
    rolled = (daily.set_index("day").groupby("customer_id")[cols]
              .rolling(window, closed="both").sum().reset_index())
    return rolled


def activity_features(points, orders, tickets):
    out = points[["customer_id", "as_of"]].copy()
    out["day"] = out["as_of"].dt.floor("D")

    od = _daily(points, orders, "ordered_at", "amount_cents")
    r7 = _rolling(od, ["n"], "7D").rename(columns={"n": "orders_7d"})
    r30 = _rolling(od, ["n", "amount"], "30D").rename(columns={"n": "orders_30d", "amount": "spend_30d_cents"})
    td = _daily(points, tickets, "opened_at")
    t30 = _rolling(td, ["n"], "30D").rename(columns={"n": "tickets_30d"})
    for part in (r7, r30, t30):
        out = out.merge(part, on=["customer_id", "day"], how="left")
    for c in ("orders_7d", "orders_30d", "spend_30d_cents", "tickets_30d"):
        out[c] = out[c].fillna(0).astype("int64")

    # time since the last order strictly before the prediction
    o = orders.sort_values("ordered_at")[["customer_id", "ordered_at"]]
    left = out[["customer_id", "as_of"]].reset_index().sort_values("as_of")
    last = pd.merge_asof(left, o, left_on="as_of", right_on="ordered_at", by="customer_id",
                         allow_exact_matches=False).set_index("index").sort_index()["ordered_at"]
    out["days_since_last_order"] = (out["as_of"] - last).dt.total_seconds() / 86400
    return out.drop(columns=["day"])


def tenure_days(points, customers):
    signup = points["customer_id"].map(customers.set_index("customer_id")["signup_at"])
    return (points["as_of"] - signup).dt.total_seconds() / 86400
