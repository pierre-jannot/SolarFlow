def get_duplicates_index(df, subset):
    """Vérifie que les dates du pipeline sont cohérentes avant tout appel API.

    Args:
        start_date: date de début au format YYYY-MM-DD
        end_date: date de fin au format YYYY-MM-DD
    """
    duplicates = df[df.duplicated(subset=subset, keep="first")]
    duplicates.sort_values(subset)
    return duplicates.index