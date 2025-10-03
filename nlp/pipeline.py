"""
Colombian Spanish NLP Pipeline
Simplified NLP pipeline for entity extraction and text summarization
"""

import spacy
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EntityResult:
    """Container for entity extraction results"""
    persons: List[str]
    locations: List[str]
    organizations: List[str]
    dates: List[str]
    money: List[str]
    colombian_entities: Dict[str, List[str]]


class NLPPipeline:
    """
    NLP Pipeline for Colombian Spanish text processing
    Focuses on entity extraction and summarization
    """

    def __init__(self, model_name: str = "es_core_news_md"):
        """
        Initialize the NLP pipeline

        Args:
            model_name: spaCy model to use (es_core_news_sm or es_core_news_md)
        """
        # Load spaCy model
        try:
            self.nlp = spacy.load(model_name)
            logger.info(f"Loaded spaCy model: {model_name}")
        except OSError:
            logger.warning(f"Model {model_name} not found. Attempting download...")
            try:
                import subprocess
                subprocess.run(
                    ["python", "-m", "spacy", "download", model_name],
                    check=True,
                    capture_output=True
                )
                self.nlp = spacy.load(model_name)
                logger.info(f"Successfully downloaded and loaded: {model_name}")
            except Exception as e:
                logger.error(f"Failed to download model: {e}")
                raise RuntimeError(f"Could not load spaCy model '{model_name}'. "
                                 f"Install with: python -m spacy download {model_name}")

        # Colombian-specific entity patterns
        self._initialize_colombian_patterns()

    def _initialize_colombian_patterns(self):
        """Initialize Colombian-specific entity patterns"""

        # Political figures and government
        self.colombian_political = {
            'Gustavo Petro', 'Francia Márquez', 'Iván Duque',
            'Juan Manuel Santos', 'Álvaro Uribe', 'Sergio Fajardo',
            'Claudia López', 'Daniel Quintero', 'Jorge Iván Ospina'
        }

        # Government institutions
        self.colombian_institutions = {
            'Presidencia', 'Congreso', 'Senado', 'Cámara de Representantes',
            'Corte Suprema', 'Corte Constitucional', 'Fiscalía',
            'Procuraduría', 'Contraloría', 'Banco de la República',
            'DANE', 'MinDefensa', 'MinHacienda', 'MinSalud', 'MinEducación',
            'Policía Nacional', 'Ejército Nacional', 'Armada Nacional'
        }

        # Major Colombian cities
        self.colombian_cities = {
            'Bogotá', 'Medellín', 'Cali', 'Barranquilla', 'Cartagena',
            'Cúcuta', 'Bucaramanga', 'Pereira', 'Santa Marta', 'Villavicencio',
            'Ibagué', 'Pasto', 'Manizales', 'Neiva', 'Armenia'
        }

        # Colombian departments
        self.colombian_departments = {
            'Antioquia', 'Valle del Cauca', 'Cundinamarca', 'Santander',
            'Atlántico', 'Bolívar', 'Nariño', 'Cauca', 'Meta', 'Arauca',
            'Putumayo', 'Chocó', 'Amazonas', 'Guaviare', 'Vaupés', 'Vichada'
        }

        # Colombian companies
        self.colombian_companies = {
            'Ecopetrol', 'Avianca', 'Grupo Éxito', 'Bancolombia',
            'Grupo Argos', 'Grupo Sura', 'Bavaria', 'Postobón',
            'Alpina', 'Colsubsidio', 'EPM', 'ISA', 'Nutresa'
        }

        # Armed groups and conflict actors
        self.conflict_actors = {
            'FARC', 'ELN', 'Clan del Golfo', 'Los Rastrojos',
            'paramilitares', 'guerrilla', 'disidencias'
        }

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities from text with Colombian-specific enhancements

        Args:
            text: Input text to analyze

        Returns:
            Dictionary containing extracted entities by type:
            - persons: List of person names
            - locations: List of location names
            - organizations: List of organization names
            - dates: List of dates
            - money: List of monetary amounts
            - political_figures: Colombian political figures
            - institutions: Colombian government institutions
            - cities: Colombian cities
            - companies: Colombian companies
            - conflict_actors: Armed groups and conflict actors

        Example:
            >>> pipeline = NLPPipeline()
            >>> entities = pipeline.extract_entities("Gustavo Petro visitó Medellín ayer")
            >>> print(entities['political_figures'])
            ['Gustavo Petro']
            >>> print(entities['cities'])
            ['Medellín']
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to extract_entities")
            return self._empty_entity_dict()

        try:
            # Process text with spaCy
            doc = self.nlp(text)

            # Initialize entity containers
            entities = {
                'persons': [],
                'locations': [],
                'organizations': [],
                'dates': [],
                'money': [],
                'percentages': [],
                'political_figures': [],
                'institutions': [],
                'cities': [],
                'departments': [],
                'companies': [],
                'conflict_actors': []
            }

            # Extract standard spaCy entities
            for ent in doc.ents:
                if ent.label_ == 'PER' or ent.label_ == 'PERSON':
                    entities['persons'].append(ent.text)
                elif ent.label_ in ['LOC', 'GPE', 'LOCATION']:
                    entities['locations'].append(ent.text)
                elif ent.label_ == 'ORG' or ent.label_ == 'ORGANIZATION':
                    entities['organizations'].append(ent.text)
                elif ent.label_ == 'DATE':
                    entities['dates'].append(ent.text)
                elif ent.label_ == 'MONEY':
                    entities['money'].append(ent.text)
                elif ent.label_ == 'PERCENT':
                    entities['percentages'].append(ent.text)

            # Enhance with Colombian-specific entities
            text_lower = text.lower()

            # Check for political figures
            for figure in self.colombian_political:
                if figure.lower() in text_lower:
                    entities['political_figures'].append(figure)

            # Check for institutions
            for institution in self.colombian_institutions:
                if institution.lower() in text_lower:
                    entities['institutions'].append(institution)

            # Check for cities
            for city in self.colombian_cities:
                if city.lower() in text_lower:
                    entities['cities'].append(city)

            # Check for departments
            for dept in self.colombian_departments:
                if dept.lower() in text_lower:
                    entities['departments'].append(dept)

            # Check for companies
            for company in self.colombian_companies:
                if company.lower() in text_lower:
                    entities['companies'].append(company)

            # Check for conflict actors
            for actor in self.conflict_actors:
                if actor.lower() in text_lower:
                    entities['conflict_actors'].append(actor)

            # Deduplicate all lists
            for key in entities:
                entities[key] = list(set(entities[key]))

            logger.info(f"Extracted {sum(len(v) for v in entities.values())} total entities")
            return entities

        except Exception as e:
            logger.error(f"Error extracting entities: {e}", exc_info=True)
            return self._empty_entity_dict()

    def summarize(self, text: str, max_sentences: int = 3) -> str:
        """
        Generate a summary of the text using extractive summarization

        Args:
            text: Input text to summarize
            max_sentences: Maximum number of sentences in summary (default: 3)

        Returns:
            Summary text containing the most important sentences

        Example:
            >>> pipeline = NLPPipeline()
            >>> text = "Long article text here..."
            >>> summary = pipeline.summarize(text, max_sentences=2)
            >>> print(summary)
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to summarize")
            return ""

        try:
            # Process text with spaCy
            doc = self.nlp(text)

            # Get sentences
            sentences = list(doc.sents)

            # If text is already short, return as-is
            if len(sentences) <= max_sentences:
                return text.strip()

            # Score sentences based on multiple factors
            sentence_scores = []

            for i, sent in enumerate(sentences):
                score = 0.0

                # Factor 1: Entity density (sentences with more entities are more important)
                entity_count = len([ent for ent in sent.ents])
                score += entity_count * 2.0

                # Factor 2: Position (earlier sentences are often more important)
                position_score = 1.0 / (i + 1)  # Decreases with position
                score += position_score * 3.0

                # Factor 3: Sentence length (avoid too short or too long)
                length = len(sent)
                if 50 <= length <= 200:  # Optimal length range
                    score += 1.0
                elif length < 20:  # Penalize very short sentences
                    score -= 1.0

                # Factor 4: Proper noun count (sentences with names/places are important)
                proper_noun_count = sum(1 for token in sent if token.pos_ == 'PROPN')
                score += proper_noun_count * 1.5

                # Factor 5: Verb count (actionable sentences are important)
                verb_count = sum(1 for token in sent if token.pos_ == 'VERB')
                score += verb_count * 0.5

                # Factor 6: Colombian-specific entities boost
                sent_text = sent.text.lower()
                colombian_entity_count = 0

                for entity_set in [self.colombian_political, self.colombian_institutions,
                                 self.colombian_cities, self.colombian_companies]:
                    for entity in entity_set:
                        if entity.lower() in sent_text:
                            colombian_entity_count += 1

                score += colombian_entity_count * 2.5

                sentence_scores.append((score, sent.text.strip(), i))

            # Sort by score (descending) and select top sentences
            sentence_scores.sort(key=lambda x: x[0], reverse=True)
            top_sentences = sentence_scores[:max_sentences]

            # Re-order by original position to maintain narrative flow
            top_sentences.sort(key=lambda x: x[2])

            # Extract just the text
            summary_sentences = [sent_text for _, sent_text, _ in top_sentences]
            summary = ' '.join(summary_sentences)

            logger.info(f"Generated summary with {len(summary_sentences)} sentences "
                       f"from {len(sentences)} total sentences")

            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {e}", exc_info=True)
            # Return first few sentences as fallback
            try:
                doc = self.nlp(text)
                sentences = list(doc.sents)[:max_sentences]
                return ' '.join([sent.text for sent in sentences])
            except:
                return text[:500] + "..." if len(text) > 500 else text

    def _empty_entity_dict(self) -> Dict[str, List[str]]:
        """Return empty entity dictionary structure"""
        return {
            'persons': [],
            'locations': [],
            'organizations': [],
            'dates': [],
            'money': [],
            'percentages': [],
            'political_figures': [],
            'institutions': [],
            'cities': [],
            'departments': [],
            'companies': [],
            'conflict_actors': []
        }

    def process(self, text: str, include_summary: bool = True) -> Dict:
        """
        Process text with both entity extraction and summarization

        Args:
            text: Input text to process
            include_summary: Whether to include summary (default: True)

        Returns:
            Dictionary containing entities and optionally summary

        Example:
            >>> pipeline = NLPPipeline()
            >>> result = pipeline.process("Article text here...")
            >>> print(result['entities']['persons'])
            >>> print(result['summary'])
        """
        result = {
            'entities': self.extract_entities(text)
        }

        if include_summary:
            result['summary'] = self.summarize(text)

        return result


# Convenience function for quick usage
def create_pipeline(model_name: str = "es_core_news_md") -> NLPPipeline:
    """
    Create and return an NLP pipeline instance

    Args:
        model_name: spaCy model to use

    Returns:
        Initialized NLPPipeline instance
    """
    return NLPPipeline(model_name=model_name)
