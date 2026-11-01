"""Who is in the experiment (EXPERIMENT.md section 3).

The experiment is the users the assignment service randomized (assignments.method = "hash"); an account whose
variant was set by hand in the feature-flag console (method = "override") was not randomized and is not in it.
Bot traffic is excluded from both arms by the rule type of the platform's flags (docs/BOT_SCREENING.md): a flag of a
rule that looks only at who the client is excludes the user, whenever it was raised; a rule that reads what the user
did during the experiment excludes no one.
"""

CLIENT_RULES = frozenset({"ua_crawler"})     # crawler user agent or data-centre network, seen on the first request
BEHAVIOUR_RULES = frozenset({"velocity"})    # counts module_click events: the carousel's arrows trip it in that arm


def experiment_users(assignments, bot_flags):
    """One row per experiment user (user_id, variant, assigned_at): hash-assigned, without a client-rule flag."""
    unknown = set(bot_flags["rule"]) - CLIENT_RULES - BEHAVIOUR_RULES
    if unknown:
        raise ValueError(f"bot rule(s) {sorted(unknown)} not classified: classify each by docs/BOT_SCREENING.md")
    randomized = assignments[assignments["method"] == "hash"]
    bots = bot_flags.loc[bot_flags["rule"].isin(CLIENT_RULES), "user_id"]
    users = randomized[~randomized["user_id"].isin(bots)]
    return users[["user_id", "variant", "assigned_at"]].reset_index(drop=True)
