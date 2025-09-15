"""
Text preprocessing for Colombian Spanish
"""

import re
import unicodedata
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class TextPreprocessor:
    """
    Text preprocessing specifically for Colombian Spanish content
    """

    def __init__(self):
        self.colombian_abbreviations = {
            'Dr.': 'Doctor',
            'Dra.': 'Doctora',
            'Lic.': 'Licenciado',
            'Ing.': 'Ingeniero',
            'Sr.': 'Señor',
            'Sra.': 'Señora',
            'Gral.': 'General',
            'Col.': 'Coronel',
            'Cnel.': 'Coronel',
            'Tte.': 'Teniente',
            'Pdte.': 'Presidente',
            'Min.': 'Ministro',
            'Gob.': 'Gobernador',
            'Alc.': 'Alcalde',
            'Dept.': 'Departamento',
            'Mpio.': 'Municipio',
            'Cía.': 'Compañía',
            'S.A.': 'Sociedad Anónima',
            'Ltda.': 'Limitada',
            'E.P.M.': 'Empresas Públicas de Medellín',
            'E.T.B.': 'Empresa de Telecomunicaciones de Bogotá'
        }

    def clean(self, text: str) -> str:
        """
        Clean text while preserving Colombian Spanish characteristics

        Args:
            text: Raw text input

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove HTML tags if present
        text = re.sub(r'<[^>]+>', ' ', text)

        # Normalize unicode characters
        text = unicodedata.normalize('NFKD', text)

        # Remove control characters but keep Spanish characters
        text = ''.join(char for char in text if not unicodedata.category(char).startswith('C'))

        # Fix spacing around punctuation
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        text = re.sub(r'([.,;:!?])([A-Za-záéíóúñÑ])', r'\1 \2', text)

        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)

        # Remove leading/trailing whitespace
        text = text.strip()

        return text

    def normalize_colombian(self, text: str) -> str:
        """
        Normalize Colombian Spanish text

        Args:
            text: Cleaned text

        Returns:
            Normalized text
        """
        # Expand abbreviations
        for abbr, full in self.colombian_abbreviations.items():
            text = text.replace(abbr, full)

        # Normalize Colombian number formats
        # Convert 1.000.000 to 1000000 (Colombian thousand separator)
        text = re.sub(r'(\d+)\.(\d{3})', r'\1\2', text)

        # Normalize currency mentions
        text = re.sub(r'\$\s*([0-9.,]+)\s*(?:millones?|M)', r'\1 millones de pesos', text)
        text = re.sub(r'\$\s*([0-9.,]+)\s*(?:mil|K)', r'\1 mil pesos', text)
        text = re.sub(r'\$\s*([0-9.,]+)', r'\1 pesos', text)

        # Normalize Colombian date formats
        # Convert "15 de enero de 2024" to standard format
        months = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
        }

        for month_name, month_num in months.items():
            pattern = fr'(\d{{1,2}}) de {month_name} de (\d{{4}})'
            text = re.sub(pattern, fr'\1/{month_num}/\2', text, flags=re.IGNORECASE)

        return text

    def remove_stopwords(self, text: str, keep_important: bool = True) -> str:
        """
        Remove Spanish stopwords while keeping important ones for context

        Args:
            text: Input text
            keep_important: Keep stopwords important for meaning

        Returns:
            Text with stopwords removed
        """
        # Spanish stopwords to remove
        stopwords = {
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
            'y', 'o', 'pero', 'si', 'que', 'de', 'en', 'a', 'para',
            'por', 'con', 'sin', 'sobre', 'entre', 'hacia', 'hasta',
            'desde', 'durante', 'mediante', 'tras', 'ante', 'bajo'
        }

        # Important words to keep for Colombian context
        important_words = {
            'no', 'sí', 'presidente', 'gobierno', 'colombia',
            'peso', 'pesos', 'millones', 'miles'
        }

        words = text.split()
        if keep_important:
            filtered = [w for w in words if w.lower() not in stopwords or w.lower() in important_words]
        else:
            filtered = [w for w in words if w.lower() not in stopwords]

        return ' '.join(filtered)

    def segment_sentences(self, text: str) -> List[str]:
        """
        Segment text into sentences considering Spanish punctuation

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        # Handle Spanish question and exclamation marks
        text = re.sub(r'¿([^?]+)\?', r'¿\1?', text)
        text = re.sub(r'¡([^!]+)!', r'¡\1!', text)

        # Split on sentence endings
        sentences = re.split(r'[.!?]+', text)

        # Clean and filter
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def extract_quotes(self, text: str) -> List[str]:
        """
        Extract quoted text (important for news articles)

        Args:
            text: Input text

        Returns:
            List of quoted strings
        """
        # Match various quote styles used in Spanish
        patterns = [
            r'"([^"]+)"',  # Double quotes
            r"'([^']+)'",  # Single quotes
            r'«([^»]+)»',  # Spanish angle quotes
            r'"([^"]+)"',  # Curved quotes
        ]

        quotes = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            quotes.extend(matches)

        return quotes