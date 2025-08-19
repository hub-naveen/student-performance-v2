import os
import sys
import json
import pandas as pd
from typing import Dict, Any


def validate_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    report: Dict[str, Any] = {}

    # Shape
    report['num_rows'] = int(df.shape[0])
    report['num_columns'] = int(df.shape[1])

    # Column names and types
    report['columns'] = {col: str(dtype) for col, dtype in df.dtypes.items()}

    # Missing values
    report['missing_per_column'] = df.isna().sum().to_dict()
    report['missing_total'] = int(df.isna().sum().sum())

    # Duplicates
    if 'student_id' in df.columns:
        report['duplicate_student_id_count'] = int(df.duplicated(subset=['student_id']).sum())
    else:
        report['duplicate_rows_count'] = int(df.duplicated().sum())

    # Basic numeric ranges/outliers
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    report['numeric_summary'] = {}
    for col in numeric_cols:
        series = df[col]
        summary = {
            'min': float(series.min()) if not series.empty else None,
            'max': float(series.max()) if not series.empty else None,
            'mean': float(series.mean()) if not series.empty else None,
            'std': float(series.std()) if not series.empty else None,
        }
        # Simple outlier flags for expected ranges
        if col in ['Attendance', 'Previous_Scores']:
            out_of_range = int(((series < 0) | (series > 100)).sum())
            summary['out_of_range_count'] = out_of_range
        report['numeric_summary'][col] = summary

    # Expected columns
    expected_columns = [
        'student_id', 'Gender', 'age', 'Previous_Scores', 'Attendance', 'Hours_Studied',
        'Teacher_Feedback', 'Parental_Involvement', 'Access_to_Resources', 'Extracurricular_Activities',
        'Sleep_Hours', 'Physical_Activity', 'Internet_Access', 'Tutoring_Sessions', 'Family_Income',
        'School_Type', 'Peer_Influence', 'Learning_Disabilities', 'Parental_Education_Level',
        'Distance_from_Home'
    ]
    report['missing_expected_columns'] = [c for c in expected_columns if c not in df.columns]

    return report


def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    data_dir = os.path.join(base_dir, 'data')
    csv_path = os.path.join(data_dir, 'StudentPerformance_with_names.csv')
    if not os.path.exists(csv_path):
        print(f"Dataset not found at {csv_path}")
        sys.exit(1)

    df = pd.read_csv(csv_path)
    # Normalize duplicated header issue if present (e.g., duplicate 'Physical_Activity')
    df.columns = [c.strip() for c in df.columns]
    # De-duplicate any repeated columns names by keeping the first occurrence
    seen = set()
    deduped_columns = []
    for c in df.columns:
        if c not in seen:
            deduped_columns.append(c)
            seen.add(c)
    if len(deduped_columns) != len(df.columns):
        df = df.loc[:, deduped_columns]

    report = validate_dataset(df)
    report_path = os.path.join(base_dir, 'reports', 'data_validation_report.json')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    print(f"Validation report written to {report_path}")


if __name__ == '__main__':
    main()


