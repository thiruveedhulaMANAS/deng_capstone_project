import importlib.util
import os
import pandas as pd
import inspect
import re
import numpy as np

def detect_hardcoded_return(func, expected_output):
    try:
        source = inspect.getsource(func).strip().lower().replace(" ", "")
        cleaned_output = repr(expected_output).replace(" ", "").lower().replace("'", "\"")

        if f"return{cleaned_output}" in source:
            return True

        assignments = re.findall(r'(\w+)=([\[\(\{].*?[\]\)\}])', source)
        for var, value in assignments:
            if repr(expected_output).replace(" ", "").lower() == value.replace(" ", "").lower() and f"return{var}" in source:
                return True
        return False
    except:
        return False

def test_student_code(solution_path, customers_path, transactions_path):
    spec = importlib.util.spec_from_file_location("student_module", solution_path)
    student_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(student_module)

    student = student_module.CustomerTransactionProcessor()

    results = []

    try:
        customers_df = student.load_customers(customers_path)
        transactions_df = student.load_transactions(transactions_path)
        assert isinstance(customers_df, pd.DataFrame)
        assert isinstance(transactions_df, pd.DataFrame)
        results.append("✅ Step 1: Data loaded successfully")
    except Exception as e:
        results.append(f"❌ Step 1: Data loading failed: {e}")
        print("\n".join(results))
        return

    try:
        cleaned_df = student.clean_transaction_data(transactions_df.copy())
        if cleaned_df.isnull().sum().sum() > 0:
            raise Exception("Nulls remain after cleaning")
        results.append("✅ Step 2: Null handling passed")

        if cleaned_df.duplicated().sum() > 0:
            raise Exception("Duplicates still present after cleaning")
        results.append("✅ Step 3: Duplicate removal passed")
    except Exception as e:
        results.append(f"❌ Step 2/3: Cleaning failed: {e}")

    try:
        merged = student.merge_data(transactions_df, customers_df)
        expected_cols = {"CustomerID", "Product", "Quantity", "Amount", "CustomerName", "MembershipLevel", "TotalAmount"}
        if not expected_cols.issubset(set(merged.columns)):
            raise Exception("Expected merged columns missing")
        if merged.shape[0] < 1:
            raise Exception("Merged DataFrame is empty")
        results.append("✅ Step 4: Merge operation successful")
    except Exception as e:
        results.append(f"❌ Step 4: Merge failed: {e}")

    try:
        total_by_membership = student.calculate_total_by_membership(merged)
        if "MembershipLevel" not in total_by_membership.columns or "TotalSpent" not in total_by_membership.columns:
            raise Exception("Output columns missing")
        if total_by_membership.shape[0] == 0:
            raise Exception("Empty result - possibly hardcoded")
        if detect_hardcoded_return(student.calculate_total_by_membership, total_by_membership):
            raise Exception("Hardcoded return detected")
        results.append("✅ Step 5: Aggregation by MembershipLevel passed with anti-cheat")
    except Exception as e:
        results.append(f"❌ Step 5: Aggregation failed: {e}")

    print("\n".join(results))

if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(__file__))
    solution_path = os.path.join(base, "student_workspace", "solution.py")
    customers_path = os.path.join(base, "data", "customers.csv")
    transactions_path = os.path.join(base, "data", "transactions.csv")
    print(customers_path)
    test_student_code(solution_path, customers_path, transactions_path)
