1. Data Processing Flow

    Read CSV bank statement
    Parse transactions with dates, descriptions, debits, and credits
    Classify transactions based on rules from YAML configuration
    Generate summary reports and visualizations

2. Transaction Classification Rules

    Income:

    All credited amounts (money coming in)
    Includes E-transfers received, tax refunds, fee refunds
    Excludes internal transfers
    
    Expenses:

    All debited amounts (money going out)
    Includes E-transfers sent, tax payments, fees paid
    Excludes internal transfers and salary entries
    Special handling for purchases (second-pass classification)

3. Key Features

    Automated Classification:

    Uses keyword-based rules from YAML file
    Configurable and easy to maintain
    Handles special cases (E-transfers, Salary)
    
    Reporting:

    Income distribution (pie chart)
    Expense distribution (pie chart)
    Monthly trends (line chart)
    CSV summaries in output folder:
    Transaction summary
    Income breakdown
    Expense breakdown
    Monthly summary

4. Data Visualization

    Interactive web dashboard using Flask
    Plotly charts for visualization
    Summary cards showing:
    Total Income
    Total Expenses
    Net Savings


5. Error Handling
    Tracks unclassified ("Other") transactions
    Prints debug information for verification
    Maintains transaction history in CSV format