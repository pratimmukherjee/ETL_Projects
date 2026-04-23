import pandas as pd
import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime

# ---------------- LOG FUNCTION ---------------- #
def log_progress(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open("code_log.txt", "a") as f:
        f.write(f"{timestamp} : {message}\n")

# ---------------- EXTRACT ---------------- #
def extract(url, table_attribs):
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'html.parser')

    # Find the heading
    heading = soup.find('span', {'id': 'By_market_capitalization'})

    # Find the next table after the heading
    table = heading.find_next('table')

    rows = table.find_all('tr')

    data = []
    for row in rows[1:]:
        cols = row.find_all('td')
        if len(cols) >= 3:
            name = cols[1].text.strip()
            
            # Clean Market Cap column
            mc = cols[2].text.strip()
            mc = mc.replace(',', '').replace('\n', '')

            data.append([name, float(mc)])

    df = pd.DataFrame(data, columns=table_attribs)
    return df

# ---------------- TRANSFORM ---------------- #
def transform(df, csv_path):
    exchange_rates = pd.read_csv(csv_path)

    df['MC_USD_Billion'] = df['MC_USD_Billion'].astype(float)

    # Extract rates
    gbp_rate = exchange_rates.loc[exchange_rates['Currency'] == 'GBP', 'Rate'].values[0]
    eur_rate = exchange_rates.loc[exchange_rates['Currency'] == 'EUR', 'Rate'].values[0]
    inr_rate = exchange_rates.loc[exchange_rates['Currency'] == 'INR', 'Rate'].values[0]

    # Add columns
    df['MC_GBP_Billion'] = (df['MC_USD_Billion'] * gbp_rate).round(2)
    df['MC_EUR_Billion'] = (df['MC_USD_Billion'] * eur_rate).round(2)
    df['MC_INR_Billion'] = (df['MC_USD_Billion'] * inr_rate).round(2)

    return df

# ---------------- LOAD CSV ---------------- #
def load_to_csv(df, output_path):
    df.to_csv(output_path, index=False)

# ---------------- LOAD DB ---------------- #
def load_to_db(df, sql_connection, table_name):
    df.to_sql(table_name, sql_connection, if_exists='replace', index=False)

# ---------------- RUN QUERIES ---------------- #
def run_queries(query_statement, sql_connection):
    output = pd.read_sql(query_statement, sql_connection)
    print(output)

# ---------------- MAIN ---------------- #

url = "https://web.archive.org/web/20230908091635/https://en.wikipedia.org/wiki/List_of_largest_banks"
table_attribs = ["Name", "MC_USD_Billion"]
csv_path = "https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBMSkillsNetwork-PY0221EN-Coursera/labs/v2/exchange_rate.csv"

output_csv = "./Largest_banks_data.csv"
db_name = "Banks.db"
table_name = "Largest_banks"

# Execution starts
log_progress("Preliminaries complete. Initiating ETL process")

df = extract(url, table_attribs)
log_progress("Data extraction complete")

df = transform(df, csv_path)
log_progress("Data transformation complete")

load_to_csv(df, output_csv)
log_progress("Data saved to CSV file")

'''conn = sqlite3.connect(db_name)
load_to_db(df, conn, table_name)
log_progress("Data loaded to database")

# Sample queries
run_queries("SELECT * FROM Largest_banks LIMIT 5", conn)
run_queries("SELECT AVG(MC_GBP_Billion) FROM Largest_banks", conn)

conn.close()'''
log_progress("ETL process complete")