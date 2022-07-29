from modules.functions import get_data_from_api

if __name__ == '__main__':
    url = 'https://sandbox-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    key = 'b54bcf4d-1bca-4e8e-9a24-22ff2c3d462c'

    get_data_from_api(
        url=url,
        key=key
    )
