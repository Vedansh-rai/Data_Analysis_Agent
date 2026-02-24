import os
import sys

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from opal import Opal

def main():
    print("🚀 Initializing Data Analysis Agent...")
    
    opal = Opal()
    test_file = os.path.join("data", "raw", "sales_data.csv")
    
    if os.path.exists(test_file):
        opal.run_pipeline(test_file)
    else:
        print(f"File not found: {test_file}")
    
if __name__ == "__main__":
    main()
