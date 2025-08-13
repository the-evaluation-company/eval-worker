"""
SOQL queries and data extraction methods.

Handles all data extraction from Salesforce Credentials_Form_Setup_Data__c object.
"""

import logging
from typing import List, Dict, Any, Optional
from simple_salesforce import Salesforce
from .client import SalesforceClient


logger = logging.getLogger(__name__)


class SalesforceExtractor:
    """Extracts data from Salesforce using SOQL queries."""
    
    def __init__(self, sf_client: SalesforceClient):
        """
        Initialize the extractor with a Salesforce client.
        
        Args:
            sf_client: Configured Salesforce client instance
        """
        self.sf_client = sf_client
        self.sf: Optional[Salesforce] = None
    
    def _get_connection(self) -> Salesforce:
        """Get Salesforce connection, establishing if needed."""
        if self.sf is None:
            self.sf = self.sf_client.connect()
        return self.sf
    
    def get_countries(self) -> List[Dict[str, Any]]:
        """
        Extract unique countries from Foreign Credential records.
        
        Uses the provided SOQL query to get unique country names.
        
        Returns:
            List[Dict]: List of country data with Key__c and count
        """
        logger.info("Extracting countries from Salesforce...")
        
        sf = self._get_connection()
        
        # Your specified SOQL query for countries
        soql = """
        SELECT Key__c, COUNT(Id) record_count
        FROM Credentials_Form_Setup_Data__c
        WHERE Type__c = 'Country' AND Key__c != null
        GROUP BY Key__c
        ORDER BY Key__c ASC
        LIMIT 300
        """
        
        try:
            result = sf.query(soql)
            countries = result['records']
            
            logger.info(f"Extracted {len(countries)} unique countries")
            return countries
            
        except Exception as e:
            logger.error(f"Failed to extract countries: {e}")
            raise
    
    def get_foreign_credentials(self) -> List[Dict[str, Any]]:
        """
        Extract Foreign Credential records.
        
        Type__c = 'Country'
        Key__c = Country Name
        Value_1__c = Foreign Credential
        Value_2__c = English Credential  
        Value_3__c = Foreign Credential Additional Information
        
        Returns:
            List[Dict]: List of foreign credential records
        """
        logger.info("Extracting foreign credentials from Salesforce...")
        
        sf = self._get_connection()
        
        soql = """
        SELECT Key__c, Value_1__c, Value_2__c, Value_3__c
        FROM Credentials_Form_Setup_Data__c
        WHERE Type__c = 'Country' AND Key__c != null
        ORDER BY Key__c ASC
        """
        
        try:
            result = sf.query_all(soql)
            credentials = result['records']
            
            logger.info(f"Extracted {len(credentials)} foreign credential records")
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to extract foreign credentials: {e}")
            raise
    
    def get_institutions(self) -> List[Dict[str, Any]]:
        """
        Extract Institution records.
        
        Type__c = 'Country Institute'
        Key__c = Country Name (FK reference)
        Value_1__c = Institution Name
        Value_2__c = Institution English Name
        Value_3__c = Institution History
        Value_4__c = Accreditation Status and Color
        
        Returns:
            List[Dict]: List of institution records
        """
        logger.info("Extracting institutions from Salesforce...")
        
        sf = self._get_connection()
        
        soql = """
        SELECT Key__c, Value_1__c, Value_2__c, Value_3__c, Value_4__c
        FROM Credentials_Form_Setup_Data__c
        WHERE Type__c = 'Country Institute' AND Key__c != null
        ORDER BY Key__c ASC
        """
        
        try:
            result = sf.query_all(soql)
            institutions = result['records']
            
            logger.info(f"Extracted {len(institutions)} institution records")
            return institutions
            
        except Exception as e:
            logger.error(f"Failed to extract institutions: {e}")
            raise
    
    def get_program_lengths(self) -> List[Dict[str, Any]]:
        """
        Extract Program Length records.
        
        Type__c = 'Program Length'
        Key__c = Country Name (FK reference)
        Value_1__c = Program Length
        
        Returns:
            List[Dict]: List of program length records
        """
        logger.info("Extracting program lengths from Salesforce...")
        
        sf = self._get_connection()
        
        soql = """
        SELECT Key__c, Value_1__c
        FROM Credentials_Form_Setup_Data__c
        WHERE Type__c = 'Program Length' AND Key__c != null
        ORDER BY Key__c ASC
        """
        
        try:
            result = sf.query_all(soql)
            programs = result['records']
            
            logger.info(f"Extracted {len(programs)} program length records")
            return programs
            
        except Exception as e:
            logger.error(f"Failed to extract program lengths: {e}")
            raise
    
    def get_grade_scales(self) -> List[Dict[str, Any]]:
        """
        Extract Grade Scale records.
        
        Type__c = 'Country Grade'
        Key__c = Country Name (FK reference)
        Value_1__c = Grade Scale
        Value_2__c = Grade Table Bifurcation Setup
        Value_3__c = Grade Scale Notes
        Value_5__c = Default Conversion Factor
        
        Returns:
            List[Dict]: List of grade scale records
        """
        logger.info("Extracting grade scales from Salesforce...")
        
        sf = self._get_connection()
        
        soql = """
        SELECT Key__c, Value_1__c, Value_2__c, Value_3__c, Value_5__c
        FROM Credentials_Form_Setup_Data__c
        WHERE Type__c = 'Country Grade' AND Key__c != null
        ORDER BY Key__c ASC
        """
        
        try:
            result = sf.query_all(soql)
            scales = result['records']
            
            logger.info(f"Extracted {len(scales)} grade scale records")
            return scales
            
        except Exception as e:
            logger.error(f"Failed to extract grade scales: {e}")
            raise
    
    def get_us_equivalencies(self) -> List[Dict[str, Any]]:
        """
        Extract US Equivalency records (standalone).
        
        Type__c = 'All Equivalncy'
        Key__c = Overall Equivalency
        Value_1__c = Overall Equivalency Description
        
        Returns:
            List[Dict]: List of US equivalency records
        """
        logger.info("Extracting US equivalencies from Salesforce...")
        
        sf = self._get_connection()
        
        soql = """
        SELECT Key__c, Value_1__c
        FROM Credentials_Form_Setup_Data__c
        WHERE Type__c = 'All Equivalncy' AND Key__c != null
        ORDER BY Key__c ASC
        """
        
        try:
            result = sf.query_all(soql)
            equivalencies = result['records']
            
            logger.info(f"Extracted {len(equivalencies)} US equivalency records")
            return equivalencies
            
        except Exception as e:
            logger.error(f"Failed to extract US equivalencies: {e}")
            raise
    
    def get_notes(self) -> List[Dict[str, Any]]:
        """
        Extract Notes records (standalone).
        
        Key__c = The actual notes content
        
        Returns:
            List[Dict]: List of notes records
        """
        logger.info("Extracting notes from Salesforce...")
        
        sf = self._get_connection()
        
        soql = """
        SELECT Key__c
        FROM Credentials_Form_Setup_Data__c
        WHERE Key__c != null AND Key__c LIKE '%note%'
        ORDER BY Key__c ASC
        """
        
        try:
            result = sf.query_all(soql)
            notes = result['records']
            
            logger.info(f"Extracted {len(notes)} notes records")
            return notes
            
        except Exception as e:
            logger.error(f"Failed to extract notes: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test the Salesforce connection and basic query capability.
        
        Returns:
            bool: True if test successful, False otherwise
        """
        try:
            sf = self._get_connection()
            
            # Test with a simple query
            result = sf.query("""
                SELECT COUNT() 
                FROM Credentials_Form_Setup_Data__c 
                LIMIT 1
            """)
            
            logger.info("Salesforce extractor connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"Salesforce extractor connection test failed: {e}")
            return False