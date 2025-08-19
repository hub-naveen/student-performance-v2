import os
import pandas as pd
import random
import string

def generate_random_names():
    """Generate random student names based on gender"""
    
    # Resolve dataset path relative to project root
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    data_dir = os.path.join(base_dir, 'data')
    cleaned_csv = os.path.join(data_dir, 'StudentPerformance_cleaned.csv')
    df = pd.read_csv(cleaned_csv)
    
    # Lists of common first names by gender
    male_names = [
        "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Christopher",
        "Charles", "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven", "Paul", "Andrew", "Joshua",
        "Kenneth", "Kevin", "Brian", "George", "Edward", "Ronald", "Timothy", "Jason", "Jeffrey", "Ryan",
        "Jacob", "Gary", "Nicholas", "Eric", "Jonathan", "Stephen", "Larry", "Justin", "Scott", "Brandon",
        "Benjamin", "Frank", "Gregory", "Raymond", "Samuel", "Patrick", "Alexander", "Jack", "Dennis", "Jerry",
        "Tyler", "Aaron", "Jose", "Adam", "Nathan", "Henry", "Douglas", "Zachary", "Peter", "Kyle",
        "Walter", "Ethan", "Jeremy", "Harold", "Kyle", "Carl", "Keith", "Roger", "Gerald", "Christian",
        "Terry", "Sean", "Austin", "Noah", "Lucas", "Jesse", "Logan", "Dylan", "Nathan", "Isaac"
    ]
    
    female_names = [
        "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen",
        "Nancy", "Lisa", "Betty", "Helen", "Sandra", "Donna", "Carol", "Ruth", "Sharon", "Michelle",
        "Laura", "Emily", "Kimberly", "Deborah", "Dorothy", "Lisa", "Nancy", "Karen", "Betty", "Helen",
        "Sandra", "Donna", "Carol", "Ruth", "Sharon", "Michelle", "Laura", "Emily", "Kimberly", "Deborah",
        "Dorothy", "Lisa", "Nancy", "Karen", "Betty", "Helen", "Sandra", "Donna", "Carol", "Ruth",
        "Sharon", "Michelle", "Laura", "Emily", "Kimberly", "Deborah", "Dorothy", "Lisa", "Nancy", "Karen",
        "Betty", "Helen", "Sandra", "Donna", "Carol", "Ruth", "Sharon", "Michelle", "Laura", "Emily",
        "Kimberly", "Deborah", "Dorothy", "Lisa", "Nancy", "Karen", "Betty", "Helen", "Sandra", "Donna",
        "Carol", "Ruth", "Sharon", "Michelle", "Laura", "Emily", "Kimberly", "Deborah", "Dorothy", "Lisa"
    ]
    
    # Lists of common last names
    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
        "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
        "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
        "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
        "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts",
        "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker", "Cruz", "Edwards", "Collins", "Reyes",
        "Stewart", "Morris", "Morales", "Murphy", "Peterson", "Bailey", "Reed", "Kelly", "Howard", "Ramos",
        "Kim", "Cox", "Ward", "Torres", "Peterson", "Gray", "Riley", "Cooper", "Richardson", "Cox",
        "Howard", "Ward", "Torres", "Peterson", "Gray", "Riley", "Cooper", "Richardson", "Cox", "Howard"
    ]
    
    # Generate random names for each student
    student_names = []
    
    for index, row in df.iterrows():
        gender = row['Gender']
        student_id = row['student_id']
        
        # Select first name based on gender
        if gender == 'Male':
            first_name = random.choice(male_names)
        else:  # Female
            first_name = random.choice(female_names)
        
        # Select random last name
        last_name = random.choice(last_names)
        
        # Generate full name
        full_name = f"{first_name} {last_name}"
        
        student_names.append({
            'student_id': student_id,
            'Gender': gender,
            'Full_Name': full_name,
            'First_Name': first_name,
            'Last_Name': last_name
        })
    
    # Create DataFrame with names
    names_df = pd.DataFrame(student_names)
    
    # Save to CSV
    names_df.to_csv(os.path.join(data_dir, 'student_names_generated.csv'), index=False)
    
    # Display sample results
    print("Sample of generated student names:")
    print("=" * 60)
    print(f"{'Student ID':<12} {'Gender':<8} {'Full Name':<25}")
    print("-" * 60)
    
    for i in range(min(20, len(names_df))):
        row = names_df.iloc[i]
        print(f"{row['student_id']:<12} {row['Gender']:<8} {row['Full_Name']:<25}")
    
    print(f"\nTotal students processed: {len(names_df)}")
    print(f"Male students: {len(names_df[names_df['Gender'] == 'Male'])}")
    print(f"Female students: {len(names_df[names_df['Gender'] == 'Female'])}")
    
    # Cross-reference with original data
    print("\nCross-reference with original dataset:")
    print("=" * 50)
    
    # Merge with original data
    merged_df = pd.merge(df, names_df[['student_id', 'Full_Name']], on='student_id', how='left')
    
    # Show some statistics
    print(f"Original dataset rows: {len(df)}")
    print(f"Names generated: {len(names_df)}")
    print(f"Merged dataset rows: {len(merged_df)}")
    
    # Save merged dataset
    merged_path = os.path.join(data_dir, 'StudentPerformance_with_names.csv')
    merged_df.to_csv(merged_path, index=False)
    print(f"\nMerged dataset saved as '{merged_path}'")
    print(f"Names only saved as '{os.path.join(data_dir, 'student_names_generated.csv')}'")
    
    return names_df, merged_df

if __name__ == "__main__":
    print("Generating random student names based on gender...")
    names_df, merged_df = generate_random_names()
