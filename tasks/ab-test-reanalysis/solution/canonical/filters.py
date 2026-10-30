"""Population filters for the readout."""


def exclude_bots(assignments, users):
    """Drop users flagged as bots from BOTH arms, before anything is counted (EXPERIMENT.md section 3)."""
    flagged = set(users.loc[users["is_bot"] == 1, "user_id"])
    return assignments[~assignments["user_id"].isin(flagged)].reset_index(drop=True)
