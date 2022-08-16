def check_dataframe(df: 'pd.DataFrame') -> bool:
    """ Function that takes a few tests in a dataframe """

    if df.empty:
        print('Dataframe is empty. Stop running')
        return False
        exit(-1)

    return True


def check_database(client: 'object', database_name: str) -> bool:
    """
    Check if a database name exists in AWS RDS

    :param client: client instance
    :param database_name: RDS Database name
    :return: boolean
    """
    db_info = client.describe_db_instances()

    if not db_info['DBInstances']:
        return True
    elif db_info['DBInstances'][0]['DBInstanceIdentifier'] == database_name:
        return False
    else:
        return True