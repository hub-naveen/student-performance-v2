import pandas as pd

def verify_specific_examples():
    """Show specific examples of cross-referencing"""
    
    # Read the merged dataset
    df = pd.read_csv('StudentPerformance_with_names.csv')
    
    print("=" * 70)
    print("SPECIFIC EXAMPLES OF CROSS-REFERENCING")
    print("=" * 70)
    
    print("\n📋 FORMAT: Student ID | Gender | Age | Full Name | Performance Data")
    print("-" * 70)
    
    # Show first 15 examples
    for i in range(15):
        row = df.iloc[i]
        print(f"{row['student_id']:<10} | {row['Gender']:<6} | {row['age']:<3} | {row['Full_Name']:<20} | Score: {row['Previous_Scores']}, Attendance: {row['Attendance']}%")
    
    print("\n" + "=" * 70)
    print("GENDER-BASED NAME VERIFICATION")
    print("=" * 70)
    
    # Show some male examples
    male_examples = df[df['Gender'] == 'Male'].head(8)
    print(f"\n🚹 MALE STUDENTS (Sample of 8):")
    for _, row in male_examples.iterrows():
        print(f"   {row['student_id']}: {row['Full_Name']} (Age: {row['age']}, Score: {row['Previous_Scores']})")
    
    # Show some female examples
    female_examples = df[df['Gender'] == 'Female'].head(8)
    print(f"\n🚺 FEMALE STUDENTS (Sample of 8):")
    for _, row in female_examples.iterrows():
        print(f"   {row['student_id']}: {row['Full_Name']} (Age: {row['age']}, Score: {row['Previous_Scores']})")
    
    print("\n" + "=" * 70)
    print("RANDOM SAMPLE VERIFICATION")
    print("=" * 70)
    
    # Show random samples
    import random
    random.seed(42)  # For reproducible results
    
    random_indices = random.sample(range(len(df)), 10)
    print(f"\n🎲 RANDOM SAMPLE (10 students):")
    for idx in random_indices:
        row = df.iloc[idx]
        print(f"   {row['student_id']}: {row['Full_Name']} ({row['Gender']}, Age: {row['age']})")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    verify_specific_examples()
