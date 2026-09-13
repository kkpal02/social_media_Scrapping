import pandas as pd

# Check if Excel file exists and show companies
excel_file = r"D:\Linedln\Company.xlsx"

try:
    df = pd.read_excel(excel_file)
    company_column = df.columns[0]
    
    print("📋 COMPANIES TO BE CHECKED:")
    print("="*50)
    print(f"Total companies: {len(df)}")
    print(f"Column name: {company_column}")
    print("\nCompany list:")
    
    for index, row in df.iterrows():
        company_name = str(row[company_column])
        print(f"{index + 1:2d}. {company_name}")
    
    print("\n✅ Excel file loaded successfully!")
    print("🚀 Ready to run verification check...")
    
except FileNotFoundError:
    print("❌ Excel file not found!")
    print(f"Expected file: {excel_file}")
    print("Please make sure the file exists and try again.")
    
except Exception as e:
    print(f"❌ Error loading Excel file: {e}")

