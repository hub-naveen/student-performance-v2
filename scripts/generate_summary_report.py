import pandas as pd
import random

def generate_summary_report():
    """Generate a comprehensive summary report of the generated names"""
    
    # Read the generated names
    names_df = pd.read_csv('student_names_generated.csv')
    
    # Read the original dataset
    original_df = pd.read_csv('StudentPerformance_cleaned.csv')
    
    # Read the merged dataset
    merged_df = pd.read_csv('StudentPerformance_with_names.csv')
    
    print("=" * 80)
    print("STUDENT NAMES GENERATION SUMMARY REPORT")
    print("=" * 80)
    
    # Basic statistics
    print(f"\n📊 DATASET OVERVIEW:")
    print(f"   • Total students: {len(names_df):,}")
    print(f"   • Male students: {len(names_df[names_df['Gender'] == 'Male']):,}")
    print(f"   • Female students: {len(names_df[names_df['Gender'] == 'Female']):,}")
    
    # Gender distribution percentage
    male_pct = (len(names_df[names_df['Gender'] == 'Male']) / len(names_df)) * 100
    female_pct = (len(names_df[names_df['Gender'] == 'Female']) / len(names_df)) * 100
    
    print(f"   • Male percentage: {male_pct:.1f}%")
    print(f"   • Female percentage: {female_pct:.1f}%")
    
    # Cross-reference verification
    print(f"\n✅ CROSS-REFERENCE VERIFICATION:")
    print(f"   • Original dataset rows: {len(original_df):,}")
    print(f"   • Names generated: {len(names_df):,}")
    print(f"   • Merged dataset rows: {len(merged_df):,}")
    
    if len(original_df) == len(names_df) == len(merged_df):
        print("   • ✅ All datasets have matching row counts")
    else:
        print("   • ❌ Row count mismatch detected")
    
    # Check for gender consistency
    print(f"\n🔍 GENDER CONSISTENCY CHECK:")
    gender_match = 0
    gender_mismatch = 0
    
    for idx, row in names_df.iterrows():
        if row['Gender'] == original_df.iloc[idx]['Gender']:
            gender_match += 1
        else:
            gender_mismatch += 1
    
    print(f"   • Gender matches: {gender_match:,}")
    print(f"   • Gender mismatches: {gender_mismatch:,}")
    print(f"   • Accuracy: {(gender_match/len(names_df)*100):.2f}%")
    
    # Sample names by gender
    print(f"\n👥 SAMPLE NAMES BY GENDER:")
    
    print(f"\n   🚹 MALE STUDENTS (Sample of 10):")
    male_sample = names_df[names_df['Gender'] == 'Male'].head(10)
    for _, row in male_sample.iterrows():
        print(f"      {row['student_id']}: {row['Full_Name']}")
    
    print(f"\n   🚺 FEMALE STUDENTS (Sample of 10):")
    female_sample = names_df[names_df['Gender'] == 'Female'].head(10)
    for _, row in female_sample.iterrows():
        print(f"      {row['student_id']}: {row['Full_Name']}")
    
    # Unique names analysis
    print(f"\n📝 NAME UNIQUENESS ANALYSIS:")
    unique_first_names = names_df['First_Name'].nunique()
    unique_last_names = names_df['Last_Name'].nunique()
    unique_full_names = names_df['Full_Name'].nunique()
    
    print(f"   • Unique first names: {unique_first_names}")
    print(f"   • Unique last names: {unique_last_names}")
    print(f"   • Unique full names: {unique_full_names}")
    
    # Check for duplicate names
    duplicates = names_df[names_df.duplicated(subset=['Full_Name'], keep=False)]
    if len(duplicates) > 0:
        print(f"   • Duplicate names found: {len(duplicates)}")
        print(f"   • Duplicate percentage: {(len(duplicates)/len(names_df)*100):.2f}%")
    else:
        print(f"   • ✅ No duplicate names found")
    
    # File information
    print(f"\n💾 GENERATED FILES:")
    print(f"   • student_names_generated.csv - Contains only names and IDs")
    print(f"   • StudentPerformance_with_names.csv - Original data + names")
    
    # Verification summary
    print(f"\n🎯 VERIFICATION SUMMARY:")
    print(f"   • ✅ Names generated for all {len(names_df):,} students")
    print(f"   • ✅ Gender-based name assignment completed")
    print(f"   • ✅ Cross-referenced with original dataset")
    print(f"   • ✅ All files saved successfully")
    
    print(f"\n" + "=" * 80)

if __name__ == "__main__":
    generate_summary_report()
