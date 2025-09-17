from flask import Blueprint, render_template
import os
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime
from pathlib import Path
import logging  # Add this import

# create a blueprint for "about"
monthly_dp = Blueprint("monthlydashboard", __name__)

def load_transactions():
    df = pd.read_csv('bankstatements/cibc_classified.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    return df


def prepare_summary_data(df):
    # Monthly summary
    df['Month'] = df['Date'].dt.strftime('%Y-%m')
    
    # Income summary (All Credits except Transfer)
    income = df[
        (df['Credit'] > 0) & 
        (df['Type'] != 'Transfer')
    ].groupby('Type')['Credit'].sum()
    income = income.sort_values(ascending=False)
    
    # Expense summary (All Debits except Transfer and Salary)
    expenses = df[
        (df['Debit'] > 0) & 
        (~df['Type'].isin(['Transfer', 'Salary']))
    ].groupby('Type')['Debit'].sum()
    expenses = expenses.sort_values(ascending=False)
    
    # Monthly trend calculation - Fixed
    # First convert Date to datetime if not already
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.strftime('%Y-%m')

    # Calculate monthly income (Credits excluding Transfers)
    monthly_income = df[
        (df['Credit'] > 0) & 
        (df['Type'] != 'Transfer')
    ].groupby('Month', as_index=False)['Credit'].sum()

    # Calculate monthly expenses (Debits excluding Transfers and Salary)
    monthly_expenses = df[
        (df['Debit'] > 0) & 
        (~df['Type'].isin(['Transfer', 'Salary']))
    ].groupby('Month', as_index=False)['Debit'].sum()

    # Merge income and expenses
    monthly_summary = pd.merge(
        monthly_income, 
        monthly_expenses, 
        on='Month', 
        how='outer'
    ).fillna(0)

    # Sort chronologically
    monthly_summary['sort_date'] = pd.to_datetime(monthly_summary['Month'])
    monthly_summary = monthly_summary.sort_values('sort_date')
    monthly_summary = monthly_summary.drop('sort_date', axis=1)

    # Setup logging
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        filename=log_dir / f'financial_dashboard_{datetime.now().strftime("%Y%m%d")}.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Log the monthly summary
    logging.info("\nMonthly Summary:")
    logging.info(monthly_summary.to_string())

    # Create output directory if it doesn't exist
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    # Export all summaries to output directory
    summary = df.groupby('Type').agg({
        'Debit': 'sum',
        'Credit': 'sum',
        'Description': 'count'
    }).round(2)
    summary.columns = ['Total Debits', 'Total Credits', 'Number of Transactions']
    
    # Save all files to output directory
    summary.to_csv(output_dir / 'transaction_summary.csv')
    income.to_frame('Amount').to_csv(output_dir / 'income_summary.csv')
    expenses.to_frame('Amount').to_csv(output_dir / 'expense_summary.csv')
    monthly_summary.to_csv(output_dir / 'monthly_summary.csv', index=False)
    
    # Track 'Other' transactions for review
    other_transactions = df[df['Type'] == 'Other']
    if not other_transactions.empty:
        print("\nUnclassified Transactions (Type = Other):")
        for _, row in other_transactions.iterrows():
            print(f"Date: {row['Date']}, Description: {row['Description']}")
            print(f"Amount: Debit=${row['Debit']:.2f}, Credit=${row['Credit']:.2f}")
            print("-" * 50)
    
    return income, expenses, monthly_summary



@monthly_dp.route("/monthlydashboard")
def monthly_dp():
    df = load_transactions()
    income, expenses, monthly_summary = prepare_summary_data(df)
    
    # Convert Series to lists for pie charts
    income_values = income.values.tolist()
    income_labels = income.index.tolist()
    expense_values = expenses.values.tolist()
    expense_labels = expenses.index.tolist()
    
    # Debug prints
    print("\nIncome Values:", income_values)
    print("Income Labels:", income_labels)
    print("\nExpense Values:", expense_values)
    print("Expense Labels:", expense_labels)
    
    # Create income pie chart with fixed size
    income_pie = go.Figure(data=[{
        'type': 'pie',
        'labels': income_labels,
        'values': income_values,
        'textinfo': 'percent+label',
        'hovertemplate': '%{label}<br>Amount: $%{value:,.2f}<br>Percentage: %{percent:.1f}%'
    }])
    income_pie.update_layout(
        title=f'Income Distribution (Total: ${sum(income_values):,.2f})',
        height=600,
        width=1000  # Added fixed width
    )
    
    # Create expense pie chart with fixed size
    expense_pie = go.Figure(data=[{
        'type': 'pie',
        'labels': expense_labels,
        'values': expense_values,
        'textinfo': 'percent+label',
        'hovertemplate': '%{label}<br>Amount: $%{value:,.2f}<br>Percentage: %{percent:.1f}%'
    }])
    expense_pie.update_layout(
        title=f'Expense Distribution (Total: ${sum(expense_values):,.2f})',
        height=650,
        width=1150  # Added fixed width
    )

    # Create monthly trend chart
    monthly_trend = go.Figure()
    monthly_trend.add_trace(go.Scatter(
        x=monthly_summary['Month'], 
        y=monthly_summary['Credit'], 
        name='Income',
        line=dict(color='#28a745')
    ))
    monthly_trend.add_trace(go.Scatter(
        x=monthly_summary['Month'], 
        y=monthly_summary['Debit'], 
        name='Expenses',
        line=dict(color='#dc3545')
    ))
    monthly_trend.update_layout(
        title='Monthly Trend',
        xaxis_title='Month',
        yaxis_title='Amount ($)',
        hovermode='x unified'
    )
    
    # Convert charts to JSON
    charts = {
        'income_pie': json.dumps(income_pie, cls=plotly.utils.PlotlyJSONEncoder),
        'expense_pie': json.dumps(expense_pie, cls=plotly.utils.PlotlyJSONEncoder),
        'monthly_trend': json.dumps(monthly_trend, cls=plotly.utils.PlotlyJSONEncoder)
    }
    
    # Calculate summaries
    total_income = income.sum()
    total_expenses = expenses.sum()
    net_savings = total_income - total_expenses
    
    return render_template('dash.html', 
                         charts=charts,
                         total_income=total_income,
                         total_expenses=total_expenses,
                         net_savings=net_savings)

if __name__ == '__main__':
    app.run(debug=True)