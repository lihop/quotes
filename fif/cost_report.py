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


class PDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Page ' + str(self.page_no()), 0, 0, 'C')


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

    rate = fx_data.iloc[date_row_index.item(
    ) - NUM_METADATA_ROWS, currency_col_index]

    return Decimal(rate).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)


def generate_fif_report(name, data):
    pdf_path = f'{name}_cost_report.pdf'
    pdf = PDF()
    pdf.add_page('L')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font('Arial', size=12)

    total_cost_nzd = Decimal(0)

    # Assume all transactions in the same currency.
    currency = data['Amount'].head(1).values[0][:3]

    # Remove time part from date column.
    data['Date'] = pd.to_datetime(data['Date'])
    data['Date'] = data['Date'].dt.date

    for date, transactions in data.groupby(data['Date']):
        exchange_rate = get_exchange_rate(currency, date)

        # Print the date and exchange rate on the day.
        date_str = str(date)
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, date_str, ln=0)
        page_width = pdf.w - pdf.l_margin - pdf.r_margin
        date_width = pdf.get_string_width(date_str) + 2
        exchange_rate_str = f"Exchange rate (NZD/{currency}): {exchange_rate}"
        exchange_rate_width = pdf.get_string_width(exchange_rate_str) + 2
        pdf.set_x(page_width - exchange_rate_width)
        pdf.set_font('Arial', '', 12)
        pdf.cell(exchange_rate_width, 10, exchange_rate_str, ln=1, align='R')

        # Table headers.
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(30, 10, 'Action', 1, 0, 'L', 1)
        pdf.cell(56, 10, 'Qty', 1, 0, 'C', 1)
        pdf.cell(60, 10, 'Amount', 1, 0, 'C', 1)
        pdf.cell(60, 10, 'Fees', 1, 0, 'C', 1)
        pdf.cell(60, 10, 'Net Transaction Value', 1, 1, 'C', 1)

        day_cost = Decimal(0)

        for index, row in transactions.iterrows():
            day_cost += Decimal(row['Net Transaction Value'][3:])
            fee_str = f'{currency} 0.00' if pd.isna(
                row['Fees']) else row['Fees']

            pdf.cell(30, 10, row['Type'], 1, 0, 'L')
            pdf.cell(56, 10, str(row['Shares']), 1, 0, 'L')
            pdf.cell(60, 10, row['Amount'], 1, 0, 'R')
            pdf.cell(60, 10, fee_str, 1, 0, 'R')
            pdf.cell(60, 10, row['Net Transaction Value'], 1, 1, 'R')

        day_cost_nzd = (day_cost * (Decimal(1) / exchange_rate)
                        ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_cost_nzd += day_cost_nzd

        pdf.set_fill_color(240, 240, 240)
        pdf.cell(206, 10, 'Total', 1, 0, 'L', 1)
        pdf.set_fill_color(255, 255, 255)
        pdf.set_font('Arial', '', 12)
        pdf.cell(60, 10, f'{currency} {day_cost}', 1, 1, 'R', 1)

        pdf.set_fill_color(255, 255, 255)
        pdf.set_font('Arial', '', 12)
        pdf.cell(
            206, 10, f'{currency} {day_cost} × (1 ÷ {exchange_rate}) = ', 1, 0, 'R', 1)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(60, 10, f'NZD {day_cost_nzd}', 1, 1, 'R', 1)

        pdf.ln(5)

        pdf.cell(266, 10, f'Total cost: NZD {total_cost_nzd}', ln=1, align='R')

        pdf.ln(10)

    pdf.output(pdf_path)


for filename in os.listdir(TRANSACTIONS_DIR):
    if filename.startswith('Transactions_') and filename.endswith('.csv'):
        name = filename[len('Transactions_'):-len('.csv')]

        csv_path = os.path.join(TRANSACTIONS_DIR, filename)
        data = pd.read_csv(csv_path)

        generate_fif_report(name, data)
