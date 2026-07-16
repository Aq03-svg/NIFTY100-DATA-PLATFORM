import pandas as pd


class DataNormaliser:

    def clean_headers(self, df):

        columns = list(df.iloc[0])

        df = df.iloc[1:].copy()

        df.columns = columns

        df.reset_index(drop=True, inplace=True)

        return df

    def normalise_dataset(self, df):

        # If the dataframe has Unnamed columns,
        # the real header is stored in the first row.

        if any("Unnamed" in str(col) for col in df.columns):

            df = self.clean_headers(df)

        # Remove completely empty rows
        df = df.dropna(how="all")

        # Remove completely empty columns
        df = df.dropna(axis=1, how="all")

        return df