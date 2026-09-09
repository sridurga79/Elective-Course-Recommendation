import os
import pandas as pd

def load_raw_data(data_dir):
    """
    Loads all required CSV files from the specified data directory.
    Returns a dictionary of raw DataFrames.
    """
    files = {
        "courses": "courses.csv",
        "prerequisites": "prerequisites.csv",
        "schedules": "schedules.csv",
        "career_paths": "career_paths.csv",
        "career_course_mapping": "career_course_mapping.csv",
        "students": "students.csv"
    }
    
    data = {}
    for key, filename in files.items():
        filepath = os.path.join(data_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Missing required data file: {filepath}")
        df = pd.read_csv(filepath)
        data[key] = df
        
    return data
