"""
Colombian Named Entity Recognition
Enhanced NER specifically for Colombian entities
"""

import re
from typing import Dict, List, Any, Optional
from spacy.tokens import Doc
import logging

logger = logging.getLogger(__name__)


class ColombianNER:
    """
    Named Entity Recognition enhanced for Colombian context
    """

    def __init__(self, nlp):
        self.nlp = nlp
        self._initialize_colombian_patterns()

    def _initialize_colombian_patterns(self):
        """Initialize Colombian-specific entity patterns"""

        # Colombian political figures
        self.political_figures = {
            'Gustavo Petro': 'PRESIDENT',
            'Francia Márquez': 'VICE_PRESIDENT',
            'Iván Duque': 'FORMER_PRESIDENT',
            'Juan Manuel Santos': 'FORMER_PRESIDENT',
            'Álvaro Uribe': 'FORMER_PRESIDENT',
            'Sergio Fajardo': 'POLITICIAN',
            'Rodolfo Hernández': 'POLITICIAN',
            'Claudia López': 'MAYOR_BOGOTA',
            'Daniel Quintero': 'MAYOR_MEDELLIN',
            'Jorge Iván Ospina': 'MAYOR_CALI'
        }

        # Government institutions
        self.institutions = {
            'Presidencia': 'GOV_EXECUTIVE',
            'Congreso': 'GOV_LEGISLATIVE',
            'Senado': 'GOV_LEGISLATIVE',
            'Cámara de Representantes': 'GOV_LEGISLATIVE',
            'Corte Suprema': 'GOV_JUDICIAL',
            'Corte Constitucional': 'GOV_JUDICIAL',
            'Fiscalía': 'GOV_PROSECUTOR',
            'Procuraduría': 'GOV_OVERSIGHT',
            'Contraloría': 'GOV_AUDIT',
            'MinDefensa': 'GOV_MINISTRY',
            'MinHacienda': 'GOV_MINISTRY',
            'MinSalud': 'GOV_MINISTRY',
            'MinEducación': 'GOV_MINISTRY',
            'MinMinas': 'GOV_MINISTRY',
            'MinAgricultura': 'GOV_MINISTRY',
            'DANE': 'GOV_STATISTICS',
            'Banco de la República': 'CENTRAL_BANK',
            'Policía Nacional': 'SECURITY_FORCE',
            'Ejército Nacional': 'SECURITY_FORCE',
            'Armada Nacional': 'SECURITY_FORCE',
            'Fuerza Aérea': 'SECURITY_FORCE'
        }

        # Armed groups and conflict actors
        self.conflict_actors = {
            'FARC': 'ARMED_GROUP',
            'ELN': 'ARMED_GROUP',
            'Clan del Golfo': 'CRIMINAL_GROUP',
            'Los Rastrojos': 'CRIMINAL_GROUP',
            'Los Pelusos': 'CRIMINAL_GROUP',
            'paramilitares': 'ARMED_GROUP',
            'guerrilla': 'ARMED_GROUP',
            'disidencias': 'ARMED_GROUP'
        }

        # Colombian companies
        self.companies = {
            'Ecopetrol': 'COMPANY_ENERGY',
            'Avianca': 'COMPANY_AIRLINE',
            'Grupo Éxito': 'COMPANY_RETAIL',
            'Bancolombia': 'COMPANY_BANKING',
            'Grupo Argos': 'COMPANY_CEMENT',
            'Grupo Sura': 'COMPANY_FINANCE',
            'Bavaria': 'COMPANY_BEVERAGE',
            'Postobón': 'COMPANY_BEVERAGE',
            'Alpina': 'COMPANY_FOOD',
            'Colsubsidio': 'COMPANY_RETAIL',
            'EPM': 'COMPANY_UTILITIES',
            'ISA': 'COMPANY_ENERGY',
            'Nutresa': 'COMPANY_FOOD'
        }

        # Colombian locations
        self.locations = {
            # Major cities
            'Bogotá': 'CITY_CAPITAL',
            'Medellín': 'CITY_MAJOR',
            'Cali': 'CITY_MAJOR',
            'Barranquilla': 'CITY_MAJOR',
            'Cartagena': 'CITY_MAJOR',
            'Cúcuta': 'CITY_MAJOR',
            'Bucaramanga': 'CITY_MAJOR',
            'Pereira': 'CITY_MAJOR',
            'Santa Marta': 'CITY_MAJOR',
            'Villavicencio': 'CITY_MAJOR',
            # Departments
            'Antioquia': 'DEPARTMENT',
            'Valle del Cauca': 'DEPARTMENT',
            'Cundinamarca': 'DEPARTMENT',
            'Santander': 'DEPARTMENT',
            'Atlántico': 'DEPARTMENT',
            'Bolívar': 'DEPARTMENT',
            'Nariño': 'DEPARTMENT',
            'Cauca': 'DEPARTMENT',
            'Meta': 'DEPARTMENT',
            'Arauca': 'DEPARTMENT',
            'Putumayo': 'DEPARTMENT',
            'Chocó': 'DEPARTMENT',
            'Amazonas': 'DEPARTMENT',
            'Guaviare': 'DEPARTMENT',
            'Vaupés': 'DEPARTMENT',
            'Vichada': 'DEPARTMENT',
            # Regions
            'Pacífico': 'REGION',
            'Caribe': 'REGION',
            'Andina': 'REGION',
            'Orinoquía': 'REGION',
            'Amazonía': 'REGION',
            'Costa Atlántica': 'REGION',
            'Eje Cafetero': 'REGION',
            'Magdalena Medio': 'REGION',
            'Urabá': 'REGION',
            'Catatumbo': 'REGION'
        }

        # Economic indicators
        self.economic_terms = {
            'peso colombiano': 'CURRENCY',
            'COP': 'CURRENCY',
            'UVR': 'ECONOMIC_UNIT',
            'UVT': 'TAX_UNIT',
            'SMMLV': 'MINIMUM_WAGE',
            'salario mínimo': 'MINIMUM_WAGE',
            'DTF': 'INTEREST_RATE',
            'IBR': 'INTEREST_RATE',
            'IPC': 'INFLATION_INDEX',
            'PIB': 'GDP',
            'TRM': 'EXCHANGE_RATE'
        }

    def extract_entities(self, doc: Doc, original_text: str = None) -> Dict[str, List[str]]:
        """
        Extract entities with Colombian enhancements

        Args:
            doc: spaCy document
            original_text: Original text before preprocessing

        Returns:
            Dictionary of entity types and their values
        """
        entities = {
            'persons': [],
            'organizations': [],
            'locations': [],
            'political_figures': [],
            'institutions': [],
            'conflict_actors': [],
            'companies': [],
            'economic_terms': [],
            'dates': [],
            'money': [],
            'percentages': []
        }

        # Use original text if provided, otherwise use doc text
        text = original_text if original_text else doc.text

        # Extract standard spaCy entities
        for ent in doc.ents:
            if ent.label_ == 'PER':
                entities['persons'].append(ent.text)
            elif ent.label_ == 'ORG':
                entities['organizations'].append(ent.text)
            elif ent.label_ in ['LOC', 'GPE']:
                entities['locations'].append(ent.text)
            elif ent.label_ == 'DATE':
                entities['dates'].append(ent.text)
            elif ent.label_ == 'MONEY':
                entities['money'].append(ent.text)
            elif ent.label_ == 'PERCENT':
                entities['percentages'].append(ent.text)

        # Enhance with Colombian-specific patterns
        entities = self._enhance_colombian_entities(text, entities)

        # Deduplicate
        for key in entities:
            entities[key] = list(set(entities[key]))

        return entities

    def _enhance_colombian_entities(self, text: str, entities: Dict) -> Dict:
        """Enhance entities with Colombian-specific patterns"""

        # Check for political figures
        for figure, role in self.political_figures.items():
            if figure.lower() in text.lower():
                entities['political_figures'].append(f"{figure} ({role})")

        # Check for institutions
        for inst, inst_type in self.institutions.items():
            if inst.lower() in text.lower():
                entities['institutions'].append(f"{inst} ({inst_type})")

        # Check for conflict actors
        for actor, actor_type in self.conflict_actors.items():
            if actor.lower() in text.lower():
                entities['conflict_actors'].append(f"{actor} ({actor_type})")

        # Check for companies
        for company, company_type in self.companies.items():
            if company.lower() in text.lower():
                entities['companies'].append(f"{company} ({company_type})")

        # Check for economic terms
        for term, term_type in self.economic_terms.items():
            if term.lower() in text.lower():
                entities['economic_terms'].append(f"{term} ({term_type})")

        # Extract Colombian ID numbers (cédula)
        cedula_pattern = r'\b\d{6,10}\b'
        cedulas = re.findall(cedula_pattern, text)
        if cedulas:
            entities['identifiers'] = cedulas

        # Extract Colombian phone numbers
        phone_pattern = r'\b(?:3\d{9}|[1-8]\d{6,7})\b'
        phones = re.findall(phone_pattern, text)
        if phones:
            entities['phone_numbers'] = phones

        return entities

    def identify_relationships(self, entities: Dict) -> List[Dict]:
        """
        Identify relationships between entities

        Args:
            entities: Dictionary of extracted entities

        Returns:
            List of identified relationships
        """
        relationships = []

        # Check for person-organization relationships
        if entities['persons'] and entities['organizations']:
            for person in entities['persons']:
                for org in entities['organizations']:
                    relationships.append({
                        'type': 'PERSON_ORG',
                        'source': person,
                        'target': org,
                        'relation': 'affiliated_with'
                    })

        # Check for location-event relationships
        if entities['locations'] and entities['conflict_actors']:
            for location in entities['locations']:
                for actor in entities['conflict_actors']:
                    relationships.append({
                        'type': 'LOCATION_ACTOR',
                        'source': location,
                        'target': actor,
                        'relation': 'operates_in'
                    })

        return relationships

    def extract_events(self, doc: Doc) -> List[Dict]:
        """
        Extract events from text

        Args:
            doc: spaCy document

        Returns:
            List of identified events
        """
        events = []

        # Event patterns
        event_verbs = ['anunciar', 'declarar', 'firmar', 'aprobar', 'rechazar',
                      'capturar', 'asesinar', 'atacar', 'protestar', 'elegir']

        for token in doc:
            if token.lemma_ in event_verbs:
                # Find subject and object
                subject = None
                obj = None

                for child in token.children:
                    if child.dep_ == 'nsubj':
                        subject = child.text
                    elif child.dep_ in ['dobj', 'obj']:
                        obj = child.text

                if subject or obj:
                    events.append({
                        'verb': token.text,
                        'lemma': token.lemma_,
                        'subject': subject,
                        'object': obj,
                        'sentence': token.sent.text
                    })

        return events