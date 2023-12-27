import os
import pandas as pd
from decimal import *
from fpdf import FPDF

TRANSACTIONS_DIR = 'transactions/'
NUM_METADATA_ROWS = 4
UNIT_ROW_INDEX = 2

# Split in to metadata and data.
# The first five rows contain metadata such as which currency unit the column represents.
# The subsequent rows contain the actual exchange rate data, with date in the first column.
fx = pd.read_excel('hb1-daily.xlsx')
fx_metadata = fx.iloc[:NUM_METADATA_ROWS]
fx_data = fx.iloc[NUM_METADATA_ROWS:]

def get_exchange_rate(currency, date):
    units = fx_metadata.iloc[UNIT_ROW_INDEX]
    try:
        currency_col_index = units.tolist().index('NZD/' + currency)
    except ValueError:
        return None, "Currency not found"
    
    input_date = pd.to_datetime(date)

    date_row_index = pd.Index([])
    while date_row_index.empty:
        date_row_index = fx_data[fx_data.iloc[:, 0] == input_date].index
        if not date_row_index.empty:
            break
    
        input_date -= pd.Timedelta(days=1)
    
        if input_date < fx_data.iloc[:, 0].min():
            return None, "Date not found in range"
    
    return fx_data.iloc[date_row_index.item() - NUM_METADATA_ROWS, currency_col_index]


def generate_fif_report(name, data):
        pdf_path = f'{name}_FIF.pdf'
        pdf = FPDF()
        pdf.add_page('L')
        pdf.set_font('Arial', size=12)

        total = 0

        for index, row in data.iterrows():
            date = str(pd.to_datetime(row['Date']).date())
            amount = row['Amount']
            fees = row['Fees']
            currency = amount[:3]
            value = row['Net Transaction Value'][4:]
            exchange_rate = get_exchange_rate(currency, date)
            nzd_val = (Decimal(value) * Decimal(1/exchange_rate)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            total += nzd_val
            line = date + ', Buy ' + amount + ' + ' + fees + ' fees * (1/' + str(exchange_rate) + ') = ' + str(nzd_val)
            pdf.cell(200, 10, txt=line, ln=True)

        line = 'Total: ' + str(nzd_val)
        pdf.cell(200, 10, txt=line, ln=True)

        pdf.output(pdf_path)


for filename in os.listdir(TRANSACTIONS_DIR):
    if filename.startswith('Transactions_') and filename.endswith('.csv'):
        name = filename[len('Transactions_'):-len('.csv')]

        csv_path = os.path.join(TRANSACTIONS_DIR, filename)
        data = pd.read_csv(csv_path)

        generate_fif_report(name, data)
