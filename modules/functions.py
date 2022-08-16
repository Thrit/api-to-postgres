import time
import json
import boto3
import configparser
import pandas as pd

from requests import Session
from sqlalchemy import create_engine
from modules.tests import *


def get_parser() -> 'Object':
    return configparser.ConfigParser()


def get_client_rds(service: str, access_key: str, secret_key: str) -> 'Object':
    return boto3.client(
        service,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )


def get_data_from_api(
        url: str,
        key: str,
):
    """
    Extracts data from the given coinmarket API
    :param url: URL to connect to the API
    :param key: Token given by the API
    """

    parser = get_parser()
    parser.read('modules/pipeline.conf')

    start = int(parser.get('api_config', 'start'))
    limit = int(parser.get('api_config', 'limit'))
    currency = parser.get('api_config', 'currency')

    parameters = {
        'start': start,
        'limit': limit,
        'convert': currency,
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
        'volume_24h',
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
        exit(-1)

    df_crypto = pd.DataFrame(cripto_dict, columns=crypto_columns)

    run_instance_rds(db_instance_identifier=parser.get('aws_boto_rds_postgres_config', 'db_instance_identifier'))

    parser = get_parser()
    parser.read('modules/pipeline.conf')

    access_key = parser.get('aws_boto_credentials', 'access_key')
    secret_key = parser.get('aws_boto_credentials', 'secret_key')

    client = get_client_rds('rds', access_key, secret_key)
    db_info = client.describe_db_instances()

    username = parser.get('aws_boto_rds_postgres_config', 'master_username')
    password = parser.get('aws_boto_rds_postgres_config', 'master_password')
    db_engine = parser.get('aws_boto_rds_postgres_config', 'db_engine')

    load_data(
        df=df_crypto,
        endpoint=db_info['DBInstances'][0]['Endpoint']['Address'],
        port=db_info['DBInstances'][0]['Endpoint']['Port'],
        user=username,
        password=password,
        database=db_engine,
    )


def run_instance_rds(db_instance_identifier: str):
    """ Verify if an instance exists and if not then it'll create one """

    parser = get_parser()
    parser.read('modules/pipeline.conf')

    access_key = parser.get('aws_boto_credentials', 'access_key')
    secret_key = parser.get('aws_boto_credentials', 'secret_key')

    dbname = parser.get('aws_boto_rds_postgres_config', 'db_name')
    username = parser.get('aws_boto_rds_postgres_config', 'master_username')
    password = parser.get('aws_boto_rds_postgres_config', 'master_password')
    db_instance_class = parser.get('aws_boto_rds_postgres_config', 'db_instance_class')
    db_engine = parser.get('aws_boto_rds_postgres_config', 'db_engine')
    db_storage = int(parser.get('aws_boto_rds_postgres_config', 'storage'))
    vpc_security_group_id = parser.get('aws_boto_rds_postgres_config', 'vpc_security_group_id')

    client = get_client_rds('rds', access_key, secret_key)

    if check_database(client=client, database_name=db_instance_identifier):

        try:
            client.create_db_instance(
                AllocatedStorage=db_storage,
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
            exit(-1)


def load_data(
        df: 'pd.Dataframe',
        endpoint='',
        port='',
        user='',
        password='',
        database=''
) -> None:
    """ Load data into a table in a RDS PostgreSQL """

    if check_dataframe(df):
        print('Valid dataframe. Proceed to load data')

    engine = f'postgresql+psycopg2://{user}:{password}@{endpoint}:{port}/{database}'
    sql_conn = create_engine(engine, echo=False)

    df.to_sql(name='coinmarket_api', con=sql_conn, if_exists='append', index=False)
