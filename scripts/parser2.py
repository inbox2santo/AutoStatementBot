import pandas as pd
import yaml
from pathlib import Path

def load_classification_rules():
    config_path = Path(__file__).parent.parent / 'config' / 'transaction_rules.yaml'
    with open(config_path, 'r') as file:
        rules = yaml.safe_load(file)
    return rules['transaction_types']

def classify_local(row):
    desc = row['Description'].lower()
    rules = load_classification_rules()
    
    # Special handling for E-Transfer credits from specific people
    if 'e-transfer' in desc.lower():
        if row['Credit'] > 0 and any(name in desc.lower() for name in ['diviyalakshmi', 'santhosh']):
            return 'Salary'
    
    # First pass classification
    for category, keywords in rules.items():
        if category != 'Purchase':  # Skip Purchase category in first pass
            if any(keyword.lower() in desc for keyword in keywords):
                return category
    
    # Check Purchase keywords
    purchase_keywords = rules.get('Purchase', [])
    if any(keyword.lower() in desc for keyword in purchase_keywords):
        # If it's a purchase, do a second pass to check other categories
        for category, keywords in rules.items():
            if category != 'Purchase':  # Check all categories except Purchase
                if any(keyword.lower() in desc for keyword in keywords):
                    return category
        return 'Purchase'  # If no other category matches, mark as Purchase
    
    return 'Other'

def main():
    # Load CSV
    df = pd.read_csv('bankstatements/cibc.csv', header=None, 
                     names=['Date', 'Description', 'Debit', 'Credit'])

    # Clean up numeric columns
    df['Debit'] = pd.to_numeric(df['Debit'], errors='coerce').fillna(0)
    df['Credit'] = pd.to_numeric(df['Credit'], errors='coerce').fillna(0)

    # Apply classification (now passing the entire row)
    df['Type'] = df.apply(classify_local, axis=1)

    # Save classified transactions
    df.to_csv('bankstatements/cibc_classified.csv', index=False)

    # Print summary
    print("\nTransaction Summary:")
    print(df.groupby('Type')[['Debit', 'Credit']].sum())

if __name__ == "__main__":
    main()