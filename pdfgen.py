from fpdf import FPDF


def generate_pdf_report(sim_df, config, output_path="backtesting_results.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # --- Simulation Inputs Summary ---
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Backtesting Simulation Inputs", ln=True)
    pdf.ln(4)
    pdf.set_font("Arial", '', 11)
    
    pdf.cell(0, 8, f"Strategy: {config.get('name', 'N/A')}", ln=True)
    pdf.cell(0, 8, f"Description: {config.get('description', 'N/A')}", ln=True)

    tickers = ', '.join(config.get('tickers', []))
    pdf.cell(0, 8, f"Tickers: {tickers}", ln=True)

    params = config.get('params', {})
    pdf.cell(0, 8, f"Short Window: {params.get('short_window', 'N/A')}", ln=True)
    pdf.cell(0, 8, f"Long Window: {params.get('long_window', 'N/A')}", ln=True)
    start_date = params.get('start_date')
    end_date = params.get('end_date')
    pdf.cell(0, 8, f"Date Range: {start_date.date()} to {end_date.date()}", ln=True)

    logic = config.get('logic', {})
    pdf.cell(0, 8, f"Buy Condition: {logic.get('buy', 'N/A')}", ln=True)
    pdf.cell(0, 8, f"Sell Condition: {logic.get('sell', 'N/A')}", ln=True)

    pdf.cell(0, 8, f"Initial Capital: ${config.get('capital', 0):,.2f}", ln=True)
    risk = config.get('risk', {})
    pdf.cell(0, 8, f"Stop Loss: {risk.get('stop_loss', 'N/A')*100:.1f}%", ln=True)
    pdf.cell(0, 8, f"Take Profit: {risk.get('take_profit', 'N/A')*100:.1f}%", ln=True)

    pdf.ln(10)

    # --- Performance Metrics ---
    cumulative_pnl = sim_df['pnl'].sum()
    initial_capital = config.get('capital', 1000000)
    effective_return = (cumulative_pnl / initial_capital) * 100
    total_operations = len(sim_df)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Backtesting Results Summary", ln=True)
    pdf.ln(2)

    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 8, f"Cumulative PnL: ${cumulative_pnl:,.2f}", ln=True)
    pdf.cell(0, 8, f"Effective Return: {effective_return:.2f} %", ln=True)
    pdf.cell(0, 8, f"Number of Total Operations: {total_operations}", ln=True)
    pdf.ln(8)

    # --- Trades Table ---
    pdf.set_font("Arial", 'B', 10)
    headers = ['Ticker', 'Trade Time', 'Return %', 'PnL ($)', 'Shares', 'Ticks', 'Exit Reason']
    col_widths = [18, 30, 20, 25, 20, 18, 45]
    for header, width in zip(headers, col_widths):
        pdf.cell(width, 8, header, border=1)
    pdf.ln()

    pdf.set_font("Arial", '', 9)
    # Format datetime for display and truncate long exit reasons
    for idx, row in sim_df.iterrows():  # fewer rows to better fit
        exit_dt = row['exit_datetime'].strftime("%Y-%m-%d %H:%M") if hasattr(row['exit_datetime'], 'strftime') else str(row['exit_datetime'])
        exit_reason = (row['exit_reason'][:40] + '...') if len(row['exit_reason']) > 43 else row['exit_reason']

        pdf.cell(col_widths[0], 6, str(row['ticker']), border=1)
        pdf.cell(col_widths[1], 6, exit_dt, border=1)
        pdf.cell(col_widths[2], 6, f"{row['return_pct']:.2f}%", border=1)
        pdf.cell(col_widths[3], 6, f"${row['pnl']:.2f}", border=1)
        pdf.cell(col_widths[4], 6, f"{row['shares']:.2f}", border=1)
        pdf.cell(col_widths[5], 6, f"{row['holding_ticks']:.1f}", border=1)
        pdf.cell(col_widths[6], 6, exit_reason, border=1)
        pdf.ln()

    pdf.output(output_path)
    print(f"PDF report generated at {output_path}")

