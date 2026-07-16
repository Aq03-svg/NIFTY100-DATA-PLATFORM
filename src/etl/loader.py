from src.utils.logger import logger
from pathlib import Path
from datetime import datetime
import pandas as pd


class ExcelLoader:

    def __init__(self, data_folder):
        self.data_folder = Path(data_folder)
        self.audit = []

    def load_file(self, filename):

        filepath = self.data_folder / filename

        try:

            df = pd.read_excel(filepath)
            from src.etl.normaliser import DataNormaliser
            normaliser = DataNormaliser()
            df = normaliser.normalise_dataset(df)

            logger.info(f"Loaded {filename}")

            self.audit.append({
                "file": filename,
                "rows": df.shape[0],
                "columns": df.shape[1],
                "status": "Success",
                "timestamp": datetime.now()
            })

            return df

        except Exception as e:

            self.audit.append({
                "file": filename,
                "rows": 0,
                "columns": 0,
                "status": f"Failed : {e}",
                "timestamp": datetime.now()
            })

            return None

    def load_all(self):

        datasets = {}

        files = self.data_folder.glob("*.xlsx")

        for file in files:

            df = self.load_file(file.name)

            if df is not None:
                datasets[file.stem] = df

        return datasets

    def generate_audit_report(self):

        audit_df = pd.DataFrame(self.audit)

        output = Path("data/output/load_audit.csv")

        audit_df.to_csv(output, index=False)

        print("\nAudit Report Generated")
        print(output)