import pandas as pd 

class AnimeDataLoader:
    def __init__(self, original_csv, processed_csv):
        self.original_csv = original_csv
        self.processed_csv = processed_csv
        
    def load_and_process(self):
        # Fixed 'on_bad_lines' and fixed 'utf-8' spelling
        df = pd.read_csv(self.original_csv, encoding="utf-8", on_bad_lines='skip').dropna()        
        required_cols = {'Name', 'Genres', 'sypnopsis'}
        missing = required_cols - set(df.columns)
        if missing:
            raise ValueError("missing Column in CSV file.")
        
        df['combined_info'] = (
            "Title: " + df["Name"] +  ".. Overview: " + df["sypnopsis"] + "Genres: " + df["Genres"]
        )
        
        df[["combined_info"]].to_csv(self.processed_csv , index = False, encoding = 'utf-8')
        
        return self.processed_csv
