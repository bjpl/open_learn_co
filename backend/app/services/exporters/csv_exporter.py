"""CSV export formatter"""

from typing import List, Dict, Any, Optional
import pandas as pd
import json
from datetime import datetime
from .base import BaseExporter


class CSVExporter(BaseExporter):
    """Export data to CSV format"""

    def __init__(self, export_dir: str = "exports"):
        super().__init__(export_dir)
        self.max_rows = 50000

    def get_file_extension(self) -> str:
        return "csv"

    async def export(
        self,
        data: List[Dict[str, Any]],
        filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Export data to CSV file

        Args:
            data: List of records to export
            filename: Base filename
            metadata: Optional metadata (ignored for CSV)

        Returns:
            Path to exported CSV file
        """
        # Sanitize data
        clean_data = self.sanitize_data(data)

        # Limit rows
        if len(clean_data) > self.max_rows:
            clean_data = clean_data[:self.max_rows]

        # Convert to DataFrame
        df = pd.DataFrame(clean_data)

        # Flatten nested structures
        df = self._flatten_dataframe(df)

        # Generate filename and path
        full_filename = self.generate_filename(filename)
        file_path = self.get_file_path(full_filename)

        # Export to CSV with UTF-8 BOM for Excel compatibility
        df.to_csv(
            file_path,
            index=False,
            encoding='utf-8-sig',  # UTF-8 with BOM
            date_format='%Y-%m-%d %H:%M:%S',
            quoting=1  # QUOTE_ALL for text fields
        )

        return str(file_path)

    def _flatten_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Flatten nested structures in DataFrame

        Args:
            df: DataFrame with potential nested data

        Returns:
            Flattened DataFrame
        """
        for col in df.columns:
            # Check if column contains lists or dicts
            if df[col].dtype == object:
                sample = df[col].iloc[0] if len(df) > 0 else None

                if isinstance(sample, (list, dict)):
                    # Convert to JSON string
                    df[col] = df[col].apply(
                        lambda x: json.dumps(x, ensure_ascii=False) if x else ""
                    )
                elif isinstance(sample, datetime):
                    # Format datetime
                    df[col] = df[col].apply(
                        lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if isinstance(x, datetime) else x
                    )

        return df

    async def export_articles(
        self,
        articles: List[Dict[str, Any]],
        filename: str = "articles"
    ) -> str:
        """
        Export articles with specific column ordering

        Args:
            articles: List of article records
            filename: Base filename

        Returns:
            Path to exported CSV file
        """
        # Define column order for articles
        column_order = [
            'title',
            'summary',
            'content',
            'source',
            'category',
            'published_date',
            'sentiment_score',
            'difficulty_level',
            'url'
        ]

        # Reorder columns if they exist
        df = pd.DataFrame(articles)
        existing_cols = [col for col in column_order if col in df.columns]
        other_cols = [col for col in df.columns if col not in column_order]
        df = df[existing_cols + other_cols]

        # Flatten and export
        df = self._flatten_dataframe(df)

        full_filename = self.generate_filename(filename)
        file_path = self.get_file_path(full_filename)

        df.to_csv(
            file_path,
            index=False,
            encoding='utf-8-sig',
            date_format='%Y-%m-%d %H:%M:%S',
            quoting=1
        )

        return str(file_path)

    async def export_vocabulary(
        self,
        vocabulary: List[Dict[str, Any]],
        filename: str = "vocabulary"
    ) -> str:
        """
        Export vocabulary with specific formatting

        Args:
            vocabulary: List of vocabulary records
            filename: Base filename

        Returns:
            Path to exported CSV file
        """
        # Define column order for vocabulary
        column_order = [
            'lemma',
            'definition',
            'translations',
            'difficulty_level',
            'part_of_speech',
            'example_sentences',
            'frequency_rank'
        ]

        df = pd.DataFrame(vocabulary)
        existing_cols = [col for col in column_order if col in df.columns]
        other_cols = [col for col in df.columns if col not in column_order]
        df = df[existing_cols + other_cols]

        df = self._flatten_dataframe(df)

        full_filename = self.generate_filename(filename)
        file_path = self.get_file_path(full_filename)

        df.to_csv(
            file_path,
            index=False,
            encoding='utf-8-sig',
            quoting=1
        )

        return str(file_path)
