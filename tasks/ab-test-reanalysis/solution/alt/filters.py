"""Population filters (alt solution): join the bot flags and keep only unflagged users, in both arms."""


def exclude_bots(assignments, users):
    flags = users[["user_id", "is_bot"]].drop_duplicates("user_id")
    joined = assignments.merge(flags, on="user_id", how="left")
    joined["is_bot"] = joined["is_bot"].fillna(0).astype(int)
    return joined[joined["is_bot"] == 0].drop(columns="is_bot").reset_index(drop=True)
