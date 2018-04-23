import os
from bs4 import BeautifulSoup
import re
import pandas as pd
import datetime
import requests


class Downloader:
    def __init__(self, *args, **kwargs):
        self.force = kwargs.pop('force') if 'force' in kwargs else False
        self.cache_path = kwargs.pop('cache_path') if 'cache_path' in kwargs else 'cache'
        self.encoding = kwargs.pop('encoding') if 'encoding' in kwargs else 'utf-8'
        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path)

    def download(self, url):
        url_hash = str(hash(url))
        path = os.path.join(self.cache_path, url_hash)

        if os.path.exists(path) and not self.force:
            with open(path, 'rb') as input_file:
                data = input_file.read()
            return data

        data = requests.get(url).text.encode(self.encoding)
        with open(path, 'wb') as output_file:
            output_file.write(data)

        return data


class CoinMarketCapFetcher(Downloader):
    index = None
    symbols = {}

    def __init__(self, *args, **kwargs):
        self.start_date = kwargs.pop('start') if 'start' in kwargs else datetime.datetime(2013, 4, 28)
        self.end_date = kwargs.pop('end') if 'end' in kwargs else datetime.datetime.today()
        super().__init__(*args, **kwargs)

    def get_symbols(self):
        self.fetch_currencies()
        return self.index['Symbol'].values.tolist()

    def get_names(self):
        self.fetch_currencies()
        return self.index['Name'].values.tolist()

    def fetch_all(self, print_progress=True):
        symbols = self.get_symbols()
        for index, symbol in enumerate(symbols):
            if print_progress:
                print('Fetching %s... (%d / %d)' % (symbol, index + 1, len(symbols)))
            self.fetch_by_symbol(symbol)

    def fetch_by_name(self, name):
        self.fetch_currencies()
        self.df_symbol = self.index[self.index['Name'] == name]
        return self._fetch_data(self.df_symbol)

    def fetch_by_symbol(self, symbol):
        self.fetch_currencies()
        self.df_symbol = self.index[self.index['Symbol'] == symbol]
        return self._fetch_data(self.df_symbol)

    def _fetch_data(self, df_symbol):
        format_date = lambda x: x.strftime('%Y%m%d')

        url = df_symbol['URL'].values[0]
        symbol = df_symbol['Symbol'].values[0]

        start = format_date(self.start_date)
        end = format_date(self.end_date)
        url += 'historical-data/?start=%s&end=%s' % (start, end)

        key = '%s-%s-%s' % (symbol, start, end)
        cache_path = os.path.join(self.cache_path, '%s.csv' % key)

        if key in self.symbols and not self.force:
            return self.symbols[key]

        if os.path.exists(cache_path) and not self.force:
            df_symbol = pd.read_csv(cache_path)
            df_symbol = df_symbol.set_index('Date')
            self.symbols[key] = df_symbol
            return df_symbol

        data = self.download(url)

        soup = BeautifulSoup(data, 'lxml')
        table = soup.find('table', {'class': 'table'})

        columns = []
        if table is not None:
            for thead in table.findAll('thead'):
                for row in thead.findAll('tr'):
                    for cell in row.findAll('th'):
                        columns.append(cell.text.strip())

        data = []
        if table is not None:
            for tbody in table.findAll('tbody'):
                for row in tbody.findAll('tr'):
                    row_values = []
                    for cell in row.findAll('td'):
                        cell_value = cell.text.strip()
                        cell_value = re.sub('\s+', ' ', cell_value)
                        row_values.append(cell_value)
                    if len(row_values) == len(columns):
                        keyvalues = {key: value for key, value in zip(columns, row_values)}
                        data.append(keyvalues)

        # Clean data
        if len(data) > 0:
            df = pd.DataFrame(data)
            df = df[['Date', 'Close', 'High', 'Low', 'Market Cap', 'Open', 'Volume']]
            df['Date'] = pd.to_datetime(df['Date'])
        else:
            df = pd.DataFrame([], columns=['Date', 'Close', 'High', 'Low', 'Market Cap', 'Open', 'Volume'])
        df = df.set_index('Date')
        df = df.sort_index()
        for column in df.columns:
            df[column] = pd.to_numeric(df[column].apply(self._clean_number), errors='coerce')

        self.symbols[key] = df
        df.to_csv(cache_path)

        return df

    def fetch_currencies(self):
        if self.index is not None and not self.force:
            return self.index

        df_path = os.path.join(self.cache_path, 'coinmarketcap_index.csv')
        if os.path.exists(df_path) and not self.force:
            df = pd.read_csv(df_path)
            self.index = df
            return df

        data = self.download('https://coinmarketcap.com/coins/views/all/')

        soup = BeautifulSoup(data, 'lxml')
        table = soup.find('table', {'class': 'table'})

        columns = []
        for thead in table.findAll('thead'):
            for row in thead.findAll('tr'):
                for cell in row.findAll('th'):
                    columns.append(cell.text.strip())

        data = []
        for tbody in table.findAll('tbody'):
            for row in tbody.findAll('tr'):
                row_values = []
                url_suffix = ''
                for cell in row.findAll('td'):
                    for link in cell.find_all('a', href=True):
                        href = link['href']
                        matches = re.findall(r'[/]{1}currencies[/]{1}(.*)[/]{1}', href)
                        if len(matches) > 0:
                            url_suffix = matches[0]
                    cell_value = cell.text.strip()
                    cell_value = re.sub('\s+', ' ', cell_value)
                    row_values.append(cell_value)

                url = 'https://coinmarketcap.com/currencies/%s/' % url_suffix
                if len(row_values) == len(columns):
                    keyvalues = {key: value for key, value in zip(columns, row_values)}
                    keyvalues['URL'] = url
                    data.append(keyvalues)

        df = pd.DataFrame(data)

        # Cleaning
        clean_number = self._clean_number
        df = df[['Name', 'Circulating Supply', 'Market Cap', 'Price', 'Symbol', 'Volume (24h)', 'URL']]
        df['Name'] = df['Name'].apply(lambda x: x.split(' ')[1])
        df['Circulating Supply'] = pd.to_numeric(df['Circulating Supply'].apply(clean_number), errors='coerce')
        df['Market Cap'] = pd.to_numeric(df['Market Cap'].apply(clean_number), errors='coerce')
        df['Price'] = pd.to_numeric(df['Price'].apply(clean_number), errors='coerce')
        df['Volume (24h)'] = pd.to_numeric(df['Volume (24h)'].apply(clean_number), errors='coerce')

        df.to_csv(df_path)
        self.index = df

        return df

    def _clean_number(self, x):
        return x.replace(',', '').replace('$', '').replace('*', '')


if __name__ == '__main__':
    fetcher = CoinMarketCapFetcher()
    fetcher.fetch_all()