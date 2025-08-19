import pandas as pd
import sys
import os

def test_dataset():
    """Test if the organized dataset works properly"""
    
    try:
        # Read the organized dataset (prefer merged names if exists)
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        data_dir = os.path.join(base_dir, 'data')
        organized_path = os.path.join(data_dir, 'StudentPerformance_organized.csv')
        merged_path = os.path.join(data_dir, 'StudentPerformance_with_names.csv')
        target_path = merged_path if os.path.exists(merged_path) else organized_path
        df = pd.read_csv(target_path)
        
        print("Dataset loaded successfully!")
        print(f"   Rows: {len(df):,}")
        print(f"   Columns: {len(df.columns)}")
        
        # Test basic operations
        print("\nTesting basic operations...")
        
        # Test filtering
        male_students = df[df['Gender'] == 'Male']
        female_students = df[df['Gender'] == 'Female']
        
        print(f"   Male students: {len(male_students):,}")
        print(f"   Female students: {len(female_students):,}")
        
        # Test sorting
        top_students = df.nlargest(5, 'Previous_Scores')
        print(f"   Top 5 students by score: {top_students['Previous_Scores'].tolist()}")
        
        # Test grouping
        avg_scores_by_gender = df.groupby('Gender', dropna=False)['Previous_Scores'].mean()
        print(f"   Average scores by gender:")
        print(avg_scores_by_gender)
        
        print("\nAll tests passed! Dataset is working properly.")
        return True
        
    except Exception as e:
        print(f"Error testing dataset: {e}")
        return False

if __name__ == "__main__":
    test_dataset()
