# coding: utf-8

# Xcelerate Data Download - Version 3.2

# Import necessary libraries
import numpy as np
import pandas as pd
import requests
from datetime import datetime
import warnings

# Ignore Warnings
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

# Define settings for the data source
rep_settings = {
    'filename': 'supply_list',
    'sheet': 'Settings',
    'columns': ['Setting', 'Value'],
    'index': None
}

supply_settings = {
    'filename': 'supply_list',
    'sheet': 'Supplies',
    'columns': ['name'],
    'index': None
}

ref_settings = {
    'filename': 'xcelerate_ref',
    'sheet': 'Supplies',
    'columns': ['name', '_id'],
    'index': None
}

# Define API endpoint and method
url = 'https://api.etainabl.com/2.0/'
method = 'consumption'

# Define headers for API request
export_headers = {
    "x-api-key": "123:abcde-12345-12345-abcde-abcde",
    "Content-Type": "application/json"
}

# Define parameters for API request
export_params = {
    'startDate': '2023-01-01',
    'endDate': '2024-01-31',
    'dataType': 'account',
    'granularity': 'monthly',
    'source': 'combined',
    'accountId': '6584fddac9ec42556203097f'
}

# Define output file settings
output_file = {
    'filename': 'Consumption',
    'sheet_name': f'{export_params["granularity"]}'
}

# Define granularity options
granularity = {
    'Yearly': 'yearly',
    'Quarterly': 'quarterly',
    'Monthly': 'monthly',
    'Weekly': 'weekly',
    'Daily': 'daily',
    'Hourly': 'hourly',
    'Half Hourly': 'halfhourly'
}

# Define source options
source = {
    'Combined': 'combined',
    'Reading': 'reading',
    'Half Hourly': 'hh',
    'Invoice': 'invoice',
    'Custom': 'custom'
}

# Define function to get data from excel file
def get_xls(settings):
    return pd.read_excel(
        f'{settings["filename"]}.xlsx',
        sheet_name=settings['sheet'],
        usecols=settings['columns'],
        index_col=settings['index']
    )

# Define function to clean data
def clean_data(supplies):
    supplies['name'] = supplies['name'].astype('object').str.strip()
    return supplies

# Define function to match ids
def match_ids(supply, ref):
    return pd.merge(supply, ref, left_on=supply_settings['columns'][0], right_on=ref_settings['columns'][0], how='inner')

# Define function to find missing ids
def missing_ids(supply, ref, supply_xids):
    failed_xids = pd.merge(supply, ref, left_on=supply_settings['columns'][0], right_on=ref_settings['columns'][0], how='left')
    failed_xids = failed_xids[~failed_xids.apply(tuple, 1).isin(supply_xids.apply(tuple, 1))]
    failed_xids['Remark'] = 'No match on Xcelerate!'
    return failed_xids

# Define function to get data from API
def get_data(xid, url, method, headers, params):
    params['accountId'] = xid
    api_url = url + method
    for _ in range(10):
        api_response = requests.get(api_url, headers=headers, params=params)
        if api_response.status_code == 200:
            return api_response
    return None

# Define function to compile data into dataframe
def compile_df(name, id, raw_data):
    supply_data = pd.json_normalize(raw_data.json(), 'data')
    supply_data['name'] = name
    supply_data['id'] = id
    return supply_data

# Define function to reformat dataframe
def reformat_df(supplies_data):
    supplies_data['timestamp'] = supplies_data['date'].str.replace('.000Z', '').str.replace('T', ' ')
    return supplies_data[['id', 'name', 'timestamp', 'consumption']]

# Define function to write dataframe to excel file
def write_to_excel(df, file_settings, export_params, source_type):
    file_core = file_settings['filename']
    data_type = export_params['granularity']
    start_date = export_params['startDate']
    end_date = export_params['endDate']
    sheet_name = f'{file_settings["sheet_name"]}-{source_type}'
    
    with pd.ExcelWriter(f'{file_core}_{data_type}_{start_date}-{end_date}.xlsx') as writer:
        df.to_excel(writer, sheet_name=sheet_name)
    
    return 'The Excel file was created successfully!'

# Main script starts here
set_table = get_xls(rep_settings)
source_type = set_table.loc[6]['Value']
export_headers['x-api-key'] = set_table.loc[0]['Value']
export_params['startDate'] = set_table.loc[3]['Value'].date().isoformat()
export_params['endDate'] = set_table.loc[4]['Value'].date().isoformat()
export_params['granularity'] = granularity[set_table.loc[5]['Value']]
export_params['source'] = source[source_type]
output_file['sheet_name'] = set_table.loc[5]['Value']
ref_table = get_xls(ref_settings)
supply_table = get_xls(supply_settings)
supply_table = clean_data(supply_table)
supply_xids = match_ids(supply_table, ref_table)
failed_xids = missing_ids(supply_table, ref_table, supply_xids)

# Open log file and write headers
with open('data_download_log.csv', 'w') as log_file:
    log_file.write('FAILED SUPPLIES\n')
    log_file.write('Index, Supply, Remark\n')

    failed_count = 1

    print('\n#################################################################################')

    if not failed_xids.empty:
        print('\nFAILED SUPPLY NUMBERS:')
        for i in failed_xids.index:
            failed_supply = failed_xids.loc[i]["name"]
            remark = failed_xids.loc[i]["Remark"]
            log_file.write(f'{failed_count}, {failed_supply}, {remark}\n')
            print(f'{failed_count} --> {failed_supply} - {remark}')
            failed_count += 1
        print('\n')
    else:
        log_file.write('None\n')

    log_file.write('\nSUCCESSFULLY DOWNLOADED SUPPLIES\n')
    log_file.write('Index,Supply,Xcelerate ID,Response,Data Size,Quantity,Total Quantity\n')

    supplies_data = pd.DataFrame()

    print('\nSUCCESSFULLY DOWNLOADED SUPPLY NUMBERS')

    for index in supply_xids.index:
        xid = supply_xids.loc[index]['_id']
        supply = supply_xids.loc[index]['name']
        supply_raw = get_data(xid, url, method, export_headers, export_params)
        if supply_raw:
            supply_data = compile_df(supply, xid, supply_raw)
            supply_qa = not supply_data.empty
            supplies_data = pd.concat([supplies_data, supply_data])
            length_raw = len(supply_raw.text)
            length_supply = len(supply_data)
            length_supplies = len(supplies_data)
            log_file.write(f'{index + 1},{supply},{xid},{length_raw},{length_supply},{length_supplies}\n')
            print(f'{index + 1} --> {supply} - {xid} - {length_supply} - {length_supplies} - {supply_qa}')

# Reformat dataframe
supplies_df = reformat_df(supplies_data)

# Write dataframe to excel file
result = write_to_excel(supplies_df, output_file, export_params, source_type)

print('\n#################################################\n')
print(f'############     {result}    ####################\n')
