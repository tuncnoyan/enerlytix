#!/usr/bin/env python
# coding: utf-8

import numpy as np
import pandas as pd
import requests
import warnings

warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

rep_settings = {
    'filename': 'supply_list',
    'sheet': 'Settings',
    'columns': ['Setting', 'Value'],
    'index': None
}

api_params = {
    'api_key': '123:abcde-12345-12345-abcde-abcde',
    'asset_limit': 1100,
    'account_limit': 10000
}

ref_filename = 'xcelerate_ref.xlsx'

third_parties_dict = {
    'esightimportcode': [],
    'esightmetercode': [],
    'esightid': []
}

def get_xls(settings):
    file_content = pd.read_excel(
        f'{settings["filename"]}.xlsx',
        sheet_name=settings['sheet'],
        usecols=settings['columns'],
        index_col=settings['index']
    )
    return file_content

def get_data(ref_type, api_params, page):
    if ref_type == 'assets':
        page_limit = api_params['asset_limit']
    else:
        page_limit = api_params['account_limit']

    accounts_url = f'https://api.etainabl.com/2.0/{ref_type}'
    headers = {"x-api-key": api_params['api_key'], "Content-Type": "application/json"}
    params = {'limit': page_limit, 'page': page}
    
    for i in range(10):
        api_response = requests.get(accounts_url, headers=headers, params=params)
        if api_response.status_code == 200:
            break
    return api_response

def create_df(ref_type, api_params):
    ref_df = pd.DataFrame()
    remaining = 1
    page = 1

    print('\n##########################################\n')

    while remaining > 0:
        ref_raw = get_data(ref_type, api_params, page)
        page_df = pd.json_normalize(ref_raw.json(), 'data')
        ref_df = pd.concat([ref_df, page_df])
    
        data_size = ref_raw.json()
        data_total = data_size['total']
        data_downloaded = data_size['limit'] + data_size['skip']
        data_remaining = data_total - data_downloaded
        table_size = len(ref_df['_id'])

        print(f'{table_size} of {data_total} {ref_type} records downloaded')
    
        remaining = data_remaining
        page += 1
    
    return ref_df

def third_party_reformat(supply_df, third_parties_dict):
    fields = list(third_parties_dict.keys())
    for index in supply_df.index:
        third_party = supply_df.iloc[index]['thirdParties']
        for i, field in enumerate(fields):
            try:
                third_parties_dict[field].append(third_party[i]['deviceId'])
            except IndexError:
                third_parties_dict[field].append(np.nan)
    
    for field in fields:
        supply_df[field] = third_parties_dict[field]
    
    supply_df = supply_df.drop('thirdParties', axis=1)

    return supply_df

def main():
    set_table = get_xls(rep_settings)
    api_params['api_key'] = set_table.loc[0]['Value']
    api_params['asset_limit'] = set_table.loc[1]['Value']
    api_params['account_limit'] = set_table.loc[2]['Value']

    site_df = create_df('assets', api_params)
    supply_df = create_df('accounts', api_params)

    result_sites = len(site_df)
    result_supplies = len(supply_df)

    supply_df = third_party_reformat(supply_df, third_parties_dict)

    df_to_excel = pd.ExcelWriter(ref_filename)
    site_df.to_excel(df_to_excel, sheet_name='Sites')
    supply_df.to_excel(df_to_excel, sheet_name='Supplies')
    df_to_excel.close()

    print('\n##########################################\n')
    print(f'****** Completed! {result_sites} sites and {result_supplies} supplies have been downloaded.')
    print('\n##########################################\n')

if __name__ == "__main__":
    main()
