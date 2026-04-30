def get_duplicates_index(df, subset):
    """Trouve et renvoie l'index des lignes dupliquées en fonction des subset choisis

    Args:
        df: dataframe pandas
        subset: colonnes à vérifier
    """
    duplicates = df[df.duplicated(subset=subset, keep="first")]
    duplicates.sort_values(subset)
    return duplicates.index

def aggregate_duplicates_mean(df, subset, cols_to_avg):
    """Réalise une moyenne des colonnes choisies sur les lignes dupliquées selon les subset choisis

    Args:
        df: dataframe pandas
        subset: colonnes présentant une duplication
        cols_to_avg: colonnes à moyenner
    """
    aggregated = (
        df.groupby(subset, as_index=False)[cols_to_avg].mean()
    )
    return aggregated

def aggregate_duplicates_auto(df, subset):
    agg_dict = {}

    for col in df.columns:
        if col in subset:
            continue
        elif df[col].dtype in ['int64', 'float64']:
            agg_dict[col] = 'mean'
        else:
            agg_dict[col] = 'first'

    return df.groupby(subset, as_index=False).agg(agg_dict)