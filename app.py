import time
import json
import boto3
import configparser
import pandas as pd

from sqlalchemy import create_engine
from requests import Session


def check_dataframe(df: 'pd.DataFrame') -> bool:
    """
    Function that takes a few tests in a dataframe
    """

    if df.empty:
        print('Dataframe is empty. Stop running')
        return False

    return True


def load_data(
        df: 'pd.Dataframe',
        endpoint='',
        port='',
        user='',
        password='',
        database=''
) -> None:
    """
    Function that will load data into a table in AWS
    """

    if check_dataframe(df):
        print('Valid dataframe. Proceed to load data')

    engine = f'postgresql+psycopg2://{user}:{password}@{endpoint}:{port}/{database}'

    sql_conn = create_engine(engine, echo=False)

    df.to_sql(name='test', con=sql_conn, if_exists='append', index=False)


def get_data_from_api(
        url: str,
        key: str,
        start='1',
        end='50',
        currency='USD'
):
    """
    Function that extracts data from a given API
    :param url: URL to connect to an API
    :param key: Token given by an API
    :param start: String - Start line
    :param end: String - Last line
    :param currency: String - Current currency
    :return:
    """

    parameters = {
        'start': start,
        'limit': end,
        'convert': currency
    }

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': key,
    }

    crypto_columns = [
        'id',
        'name',
        'symbol',
        'circulating_supply',
        'total_supply',
        'max_supply',
        'last_updated',
        'date_added',
        'price',
        'volume_24h'
    ]

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)

        id_cripto = []
        name = []
        symbol = []
        circulating_supply = []
        total_supply = []
        max_supply = []
        last_updated = []
        date_added = []
        price = []
        volume_24h = []

        for row in data['data']:
            id_cripto.append(row['id'])
            name.append(row['name'])
            symbol.append(row['symbol'])
            circulating_supply.append(row['circulating_supply'])
            total_supply.append(row['total_supply'])
            max_supply.append(row['max_supply'])
            last_updated.append(row['last_updated'])
            date_added.append(row['date_added'])
            price.append(row['quote']['USD']['price'])
            volume_24h.append(row['quote']['USD']['volume_24h'])

        cripto_dict = {
            'id': id_cripto,
            'name': name,
            'symbol': symbol,
            'circulating_supply': circulating_supply,
            'total_supply': total_supply,
            'max_supply': max_supply,
            'last_updated': last_updated,
            'date_added': date_added,
            'price': price,
            'volume_24h': volume_24h
        }

    except:
        print('Error to access API')
        exit(1)

    df_crypto = pd.DataFrame(cripto_dict, columns=crypto_columns)

    run_instance_rds(db_instance_identifier='databasetest')

    client = boto3.client('rds')
    db_info = client.describe_db_instances()

    load_data(
        df=df_crypto,
        endpoint=db_info['DBInstances'][0]['Endpoint']['Address'],
        port=db_info['DBInstances'][0]['Endpoint']['Port'],
        user=db_info['DBInstances'][0]['MasterUsername'],
        password='testpw0021',
        database='postgres'
    )


def check_database(client: 'object', database_name: str) -> bool:
    """

    :param client: AWS's instance
    :param database_name: Database name
    :return:
    """
    db_info = client.describe_db_instances()

    if not db_info['DBInstances']:
        return True
    elif db_info['DBInstances'][0]['DBInstanceIdentifier'] == database_name:
        return False
    else:
        return True


def run_instance_rds(db_instance_identifier: str):

    client = boto3.client('rds')

    parser = configparser.ConfigParser()
    parser.read('modules/pipeline.conf')

    dbname = parser.get('aws_boto_rds_postgres_config', 'db_name')
    username = parser.get('aws_boto_rds_postgres_config', 'master_username')
    password = parser.get('aws_boto_rds_postgres_config', 'master_password')
    db_instance_class = parser.get('aws_boto_rds_postgres_config', 'db_instance_class')
    db_engine = parser.get('aws_boto_rds_postgres_config', 'db_engine')
    db_storage = parser.get('aws_boto_rds_postgres_config', 'storage')
    vpc_security_group_id = parser.get('aws_boto_rds_postgres_config', 'vpc_security_group_id')

    if check_database(client=client, database_name=db_instance_identifier):

        try:
            response = client.create_db_instance(
                AllocatedStorage=int(db_storage),
                DBInstanceClass=db_instance_class,
                DBName=dbname,
                DBInstanceIdentifier=db_instance_identifier,
                Engine=db_engine,
                MasterUsername=username,
                MasterUserPassword=password,
                VpcSecurityGroupIds=[
                    vpc_security_group_id,
                ]
            )

            print('Creating database. It will take a few minutes...')
            time.sleep(360)

        except:
            print('Error in creating a database on AWS')
            exit(1)


if __name__ == '__main__':
    url = 'https://sandbox-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    key = 'b54bcf4d-1bca-4e8e-9a24-22ff2c3d462c'

    get_data_from_api(
        url=url,
        key=key
    )
