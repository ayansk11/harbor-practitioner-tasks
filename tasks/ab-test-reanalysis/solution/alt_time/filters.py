"""Population (alt_time solution): the time reading of EXPERIMENT.md section 3.

The users the assignment service randomized (method = hash; an exact repeat of a row counts once), minus every user
with a bot flag of any rule raised at or before the user's assigned_at. A flag raised that early cannot come from
anything the user did in the experiment; a flag raised later may (the velocity rule reads module clicks), and the plan
excludes no one for that. On these exports this gives the same users as excluding by rule type.
"""


def randomized_users(assignments):
    rows = assignments.drop_duplicates()
    if rows["user_id"].duplicated().any():
        raise ValueError("conflicting assignment rows for one user")
    if not rows["variant"].isin(["A", "B"]).all():
        raise ValueError("a variant other than A or B")
    return rows.loc[rows["method"] == "hash", ["user_id", "variant", "assigned_at"]]


def experiment_users(assignments, bot_flags):
    users = randomized_users(assignments)
    flags = bot_flags.merge(users[["user_id", "assigned_at"]], on="user_id", how="inner")
    before = flags.loc[flags["flagged_at"] <= flags["assigned_at"], "user_id"].drop_duplicates()
    keep = users.merge(before.to_frame(), on="user_id", how="left", indicator=True)
    return keep.loc[keep["_merge"] == "left_only", ["user_id", "variant", "assigned_at"]].reset_index(drop=True)
