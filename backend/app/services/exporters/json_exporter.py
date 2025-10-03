"""JSON export formatter"""

from typing import List, Dict, Any, Optional
import json
from datetime import datetime
from .base import BaseExporter


class JSONExporter(BaseExporter):
    """Export data to JSON format"""

    def __init__(self, export_dir: str = "exports"):
        super().__init__(export_dir)
        self.max_records = 100000

    def get_file_extension(self) -> str:
        return "json"

    async def export(
        self,
        data: List[Dict[str, Any]],
        filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Export data to JSON file

        Args:
            data: List of records to export
            filename: Base filename
            metadata: Optional metadata to include

        Returns:
            Path to exported JSON file
        """
        # Sanitize data
        clean_data = self.sanitize_data(data)

        # Limit records
        if len(clean_data) > self.max_records:
            clean_data = clean_data[:self.max_records]

        # Build export structure
        export_data = {
            "metadata": {
                "exported_at": datetime.now().isoformat(),
                "total_records": len(clean_data),
                "version": "1.0"
            },
            "data": clean_data
        }

        # Add custom metadata if provided
        if metadata:
            export_data["metadata"].update(metadata)

        # Generate filename and path
        full_filename = self.generate_filename(filename)
        file_path = self.get_file_path(full_filename)

        # Export to JSON with pretty printing
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(
                export_data,
                f,
                ensure_ascii=False,
                indent=2,
                default=self._json_serializer
            )

        return str(file_path)

    async def export_jsonl(
        self,
        data: List[Dict[str, Any]],
        filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Export data to JSON Lines format (one record per line)
        Useful for very large datasets

        Args:
            data: List of records to export
            filename: Base filename
            metadata: Optional metadata

        Returns:
            Path to exported JSONL file
        """
        # Sanitize data
        clean_data = self.sanitize_data(data)

        # Generate filename with .jsonl extension
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y-%m-%d_%H%M%S")
        safe_base = "".join(c for c in filename if c.isalnum() or c in ('-', '_'))
        full_filename = f"{safe_base}_{timestamp_str}.jsonl"
        file_path = self.get_file_path(full_filename)

        # Export to JSONL (one JSON object per line)
        with open(file_path, 'w', encoding='utf-8') as f:
            # Write metadata as first line
            if metadata:
                metadata_line = {
                    "_metadata": {
                        "exported_at": datetime.now().isoformat(),
                        "total_records": len(clean_data),
                        **metadata
                    }
                }
                f.write(json.dumps(metadata_line, ensure_ascii=False, default=self._json_serializer) + '\n')

            # Write each record as a line
            for record in clean_data:
                f.write(json.dumps(record, ensure_ascii=False, default=self._json_serializer) + '\n')

        return str(file_path)

    async def export_streaming(
        self,
        data: List[Dict[str, Any]],
        filename: str,
        chunk_size: int = 1000
    ) -> str:
        """
        Export large datasets using streaming to avoid memory issues

        Args:
            data: List of records to export
            filename: Base filename
            chunk_size: Number of records to process at once

        Returns:
            Path to exported JSON file
        """
        # Generate filename and path
        full_filename = self.generate_filename(filename)
        file_path = self.get_file_path(full_filename)

        # Write file in chunks
        with open(file_path, 'w', encoding='utf-8') as f:
            # Write metadata and opening bracket
            f.write('{\n')
            f.write('  "metadata": {\n')
            f.write(f'    "exported_at": "{datetime.now().isoformat()}",\n')
            f.write(f'    "total_records": {len(data)},\n')
            f.write('    "version": "1.0"\n')
            f.write('  },\n')
            f.write('  "data": [\n')

            # Write data in chunks
            for i, chunk in enumerate(self.chunk_data(data, chunk_size)):
                clean_chunk = self.sanitize_data(chunk)

                for j, record in enumerate(clean_chunk):
                    json_str = json.dumps(record, ensure_ascii=False, indent=4, default=self._json_serializer)
                    # Indent each line
                    indented = '\n'.join('    ' + line for line in json_str.split('\n'))
                    f.write(indented)

                    # Add comma if not last record
                    if i * chunk_size + j < len(data) - 1:
                        f.write(',\n')
                    else:
                        f.write('\n')

            # Close data array and JSON object
            f.write('  ]\n')
            f.write('}\n')

        return str(file_path)

    def _json_serializer(self, obj):
        """Custom JSON serializer for special types"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)
