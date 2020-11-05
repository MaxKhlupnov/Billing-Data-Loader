import requests
import pandas as pd
import boto3
from datetime import datetime
from io import BytesIO, StringIO
import os

CH_PASSWORD = os.environ['CH_PASSWORD']
CH_HOST = 'https://{host}:8443/?database={db}'.format(
        host= os.environ['CH_HOST'],
        db= os.environ['CH_DB'])
AUTH = {
        'X-ClickHouse-User': os.environ['CH_USER'],
        'X-ClickHouse-Key': CH_PASSWORD,
       }
CERT = './CA.pem'
BUCKET = os.environ['STORAGE_BUCKET']
FOLDER = os.environ['STORAGE_FOLDER']
TABLE = os.environ['CH_TABLE']


def request():
    url = (CH_HOST + '&query={query}').format(
        query='SELECT version()')

    res = requests.get(
        url,
        headers=AUTH,
        verify=CERT)
    res.raise_for_status()
    return res.text


def get_clickhouse_data(query, host=CH_HOST, connection_timeout=1500):
    r = requests.post(host, params={'query': query}, headers=AUTH, verify=CERT, timeout=connection_timeout)
    if r.status_code == 200:
        return r.text
    else:
        raise ValueError(r.text)


def get_clickhouse_df(query, host=CH_HOST, connection_timeout=1500):
    data = get_clickhouse_data(query, host, connection_timeout)
    df = pd.read_csv(StringIO(data), sep='\t')
    return df


def upload(table, content, host=CH_HOST):
    content = content.replace('\r\n','\n').encode('utf-8')
    query_dict = {
        'query': 'INSERT INTO ' + table + ' FORMAT TabSeparatedWithNames '
    }
    r = requests.post(host, data=content, params=query_dict, headers=AUTH, verify=CERT)
    result = r.text
    if r.status_code == 200:
        return result
    else:
        raise ValueError(r.text)

# Remove label columns
def remove_labels_columns(df: pd.DataFrame):
    for column_key in df.columns.tolist():
        if column_key.startswith('label.'):
            df.drop(column_key, axis=1, inplace=True)
    #cols_total: Set[Any] = set(df.columns)
    #diff: Set[Any] = cols_total - columns
    #df.drop(diff, axis=1, inplace=True)

# Shape Data
def shape_df(tmp_df):
    tmp_df["date"] = pd.to_datetime(tmp_df["date"]).dt.round('D')
    #tmp_df["exported_at"] = tmp_df["exported_at"].dt.round('s')
    tmp_df["pricing_quantity"]=tmp_df["pricing_quantity"].round(10)
    tmp_df["cost"]=tmp_df["cost"].round(10)
    tmp_df["credit"]=tmp_df["credit"].round(10)
    tmp_df["monetary_grant_credit"]=tmp_df["monetary_grant_credit"].round(10)
    tmp_df["volume_incentive_credit"]=tmp_df["volume_incentive_credit"].round(10)
    tmp_df["cud_credit"]=tmp_df["cud_credit"].round(10)
    tmp_df["misc_credit"]=tmp_df["misc_credit"].round(10)
    remove_labels_columns(tmp_df)
    return tmp_df

def handler(event, context):
    q = '''
    CREATE TABLE IF NOT EXISTS ''' + TABLE+'''
    (
        billing_account_id	String, 
        billing_account_name String,
        cloud_id String,
        cloud_name String,	
        folder_id String,
        folder_name	String,
        resource_id	String,
        service_id	String,
        service_name String,
        sku_id	String,
        sku_name String,
        date date,      
        currency String,	      	
        pricing_quantity decimal(25,10),
        pricing_unit String,	
        cost	decimal(25,10),
        credit	decimal(25,10),
        monetary_grant_credit 	decimal(25,10),
        volume_incentive_credit 	decimal(25,10),
        cud_credit 	decimal(25,10),
        misc_credit decimal(25,10),                
        locale String,
        updated_at	int,	        
        exported_at String
    )
    ENGINE = MergeTree
    PARTITION BY date 
    ORDER BY (date, sku_id) 
    '''
    get_clickhouse_data(q)

    q = '''select concat(replace(toString(
                        subtractDays(COALESCE(maxOrNull(date), toDate('2018-01-03')),2)
                                         ),'-',''),'.csv') from ''' + TABLE
    try:
        start_key = get_clickhouse_data(q).rstrip()
    except ValueError:
        start_key = '20180102.csv'

    session = boto3.session.Session()
    s3 = session.client(
        service_name='s3',
        endpoint_url='https://storage.yandexcloud.net'
    )

    kwargs = {"Bucket": BUCKET, "Prefix" : FOLDER, "MaxKeys" : 100, "StartAfter" : FOLDER + '/' + start_key}
    continuation_token = None
    bck_cnt=0
    while True:
        if continuation_token:
            kwargs['ContinuationToken'] = continuation_token
        obj_list = s3.list_objects_v2(**kwargs)
        try:
            for key in obj_list['Contents']:
                get_object_response = s3.get_object(Bucket=BUCKET, Key=key['Key'])['Body'].read().decode('utf-8')
                df = pd.read_csv(StringIO(get_object_response))
                shape_df(df)
                for part_dt in df["date"].unique():
                    q = '''ALTER TABLE ''' + TABLE + ''' DROP PARTITION ''' + pd.to_datetime(part_dt).strftime("'%Y-%m-%d'")
                    get_clickhouse_data(q)
                upload(
                    TABLE,
                    df.to_csv(index=False, sep='\t'))
                print('object '+ key['Key'] + ' uploaded' )
                bck_cnt = bck_cnt + 1
        except KeyError:
            print ('No objects found in Bucket ' + BUCKET + ' with prefix ' + FOLDER)
        if not obj_list.get('IsTruncated'):  # At the end of the list?
            break
        continuation_token = obj_list.get('NextContinuationToken')
    return {
        'statusCode': 200,
        'body': str(bck_cnt) + ' objects loaded',
        'isBase64Encoded': False,
    }

handler('','')