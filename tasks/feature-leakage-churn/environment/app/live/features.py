"""Feature queries of the live churn scoring service: a read-only copy of the service's `features` module.

This copy is the contract between the live service and the offline pipeline in `churn/`. It is kept for reference:
nothing in this repository imports or runs it, there is no warehouse connection here, and editing it changes nothing.

How the service uses it. A scoring request names a customer and a moment: the 06:00 batch run (trigger `batch`), or
the support desk when a ticket is opened (trigger `ticket`, at the ticket's `opened_at`). For each request the service
runs every query in QUERIES once, at the moment of the request, against the warehouse tables as they stand at that
moment, and takes the first column of the first row as the feature's value; a query that returns no row, or NULL,
gives a null value. The service then scores the 11 values with the deployed model, if one is attached, and logs them
with the request.

Parameters of every query:
    :customer_id     the request's customer
    :now             the moment of the request (the `as_of` the scoring service records for it)
    :app_minutes_7d  the product-analytics reading that came with the request, NULL when it came without one

The warehouse is PostgreSQL. Timestamps are `timestamptz` and sessions run in UTC, so INTERVAL '7 days' is exactly
7 x 86,400 seconds and EXTRACT(EPOCH FROM <interval>) is a number of seconds. The tables, and when their rows and
values are committed: docs/WAREHOUSE.md.
"""

QUERIES = {
    # orders in the 7 days before the request
    "orders_7d": """
        SELECT COUNT(*)
        FROM orders
        WHERE customer_id = :customer_id
          AND ordered_at >= :now - INTERVAL '7 days'
          AND ordered_at < :now
    """,
    # orders in the 30 days before the request
    "orders_30d": """
        SELECT COUNT(*)
        FROM orders
        WHERE customer_id = :customer_id
          AND ordered_at >= :now - INTERVAL '30 days'
          AND ordered_at < :now
    """,
    # amount of those orders, in cents (0 when there are none)
    "spend_30d_cents": """
        SELECT COALESCE(SUM(amount_cents), 0)
        FROM orders
        WHERE customer_id = :customer_id
          AND ordered_at >= :now - INTERVAL '30 days'
          AND ordered_at < :now
    """,
    # support tickets opened in the 30 days before the request
    "tickets_30d": """
        SELECT COUNT(*)
        FROM tickets
        WHERE customer_id = :customer_id
          AND opened_at >= :now - INTERVAL '30 days'
          AND opened_at < :now
    """,
    # days since the latest order before the request (NULL when there is none)
    "days_since_last_order": """
        SELECT EXTRACT(EPOCH FROM (:now - MAX(ordered_at))) / 86400.0
        FROM orders
        WHERE customer_id = :customer_id
          AND ordered_at < :now
    """,
    # days since sign-up
    "tenure_days": """
        SELECT EXTRACT(EPOCH FROM (:now - signup_at)) / 86400.0
        FROM customers
        WHERE customer_id = :customer_id
    """,
    # account status of the latest snapshot (no row: NULL)
    "status": """
        SELECT status
        FROM status_snapshots
        WHERE customer_id = :customer_id
        ORDER BY snapshot_date DESC
        LIMIT 1
    """,
    # subscription plan on the customer record
    "plan": """
        SELECT plan
        FROM customers
        WHERE customer_id = :customer_id
    """,
    # days since the last login on the customer record (NULL when the record has none)
    "days_since_last_login": """
        SELECT EXTRACT(EPOCH FROM (:now - last_login_at)) / 86400.0
        FROM customers
        WHERE customer_id = :customer_id
    """,
    # app minutes over the last 7 days: the request's own reading, else the reading of the customer's latest earlier
    # request that had one (NULL when there is none)
    "app_minutes_7d": """
        SELECT COALESCE(
            CAST(:app_minutes_7d AS double precision),
            (SELECT app_minutes_7d
             FROM scoring_points
             WHERE customer_id = :customer_id
               AND as_of < :now
               AND app_minutes_7d IS NOT NULL
             ORDER BY as_of DESC
             LIMIT 1))
    """,
    # smoothed churn rate of the customer's postcode district: (s + 20 p) / (n + 20), where p is the mean churned_30d
    # of all label rows (0.05 when there are none), and n and s are the number of label rows of customers in the same
    # district and the sum of their churned_30d
    "te_district": """
        WITH lab AS (
            SELECT l.churned_30d, c.postcode_district
            FROM labels l
            JOIN customers c ON c.customer_id = l.customer_id
        ),
        own AS (
            SELECT postcode_district
            FROM customers
            WHERE customer_id = :customer_id
        )
        SELECT (COALESCE(SUM(lab.churned_30d) FILTER (WHERE lab.postcode_district = own.postcode_district), 0)
                + 20 * COALESCE(AVG(lab.churned_30d), 0.05))
               / (COUNT(*) FILTER (WHERE lab.postcode_district = own.postcode_district) + 20)
        FROM lab CROSS JOIN own
    """,
}

FEATURES = list(QUERIES)
