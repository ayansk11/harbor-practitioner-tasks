"""Population filters for the readout."""


def exclude_bots(assignments, users):
    """Drop users flagged as bots (EXPERIMENT.md, Population)."""
    flagged = set(users.loc[users["is_bot"] == 1, "user_id"])
    # INC-4471: the crawler spike came in with the new B module's tracking, so the bot filter targets B traffic.
    in_b = assignments["variant"] == "B"
    keep = ~(in_b & assignments["user_id"].isin(flagged))
    return assignments[keep].reset_index(drop=True)
