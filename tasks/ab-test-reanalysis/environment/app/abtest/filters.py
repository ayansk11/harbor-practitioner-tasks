"""Population filters for the readout."""


def exclude_bots(assignments, bot_flags):
    """Drop bot traffic from both arms, before anything is counted (EXPERIMENT.md section 3).

    Bot traffic is every user the platform's bot screening flagged (bot_flags.csv.gz): crawlers (rule ua_crawler)
    and, since SEC-219, click-fraud bots on the related-items module (rule velocity).
    """
    flagged = set(bot_flags["user_id"])
    return assignments[~assignments["user_id"].isin(flagged)].reset_index(drop=True)
