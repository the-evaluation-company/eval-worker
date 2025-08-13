"""
Data extraction, transformation, and loading operations.

Handles the ETL process from Salesforce to SQLite.
"""

import sqlite3
import logging
import uuid
from typing import List, Dict, Any, Optional
from salesforce.extractors import SalesforceExtractor
from database.connection import get_db_connection
from utils.helpers import clean_string, validate_country_name


logger = logging.getLogger(__name__)


class DataMigrator:
    """Handles ETL operations from Salesforce to SQLite."""
    
    def __init__(self, sf_extractor: SalesforceExtractor):
        """
        Initialize the data migrator.
        
        Args:
            sf_extractor: Configured Salesforce extractor instance
        """
        self.sf_extractor = sf_extractor
    
    def run_full_migration(self) -> None:
        """
        Run the complete ETL pipeline.
        
        1. Extract countries and populate Country table
        2. Extract and load Foreign Credentials
        3. Extract and load Institutions
        4. Extract and load Program Lengths
        5. Extract and load Grade Scales
        6. Extract and load US Equivalencies
        7. Extract and load Notes
        """
        logger.info("Starting full data migration from Salesforce...")
        
        try:
            # Step 1: Countries (master reference)
            self.migrate_countries()
            
            # Step 2: Foreign Credentials
            self.migrate_foreign_credentials()
            
            # Step 3: Institutions
            self.migrate_institutions()
            
            # Step 4: Program Lengths
            self.migrate_program_lengths()
            
            # Step 5: Grade Scales
            self.migrate_grade_scales()
            
            # Step 6: US Equivalencies (standalone)
            self.migrate_us_equivalencies()
            
            # Step 7: Notes (standalone)
            self.migrate_notes()
            
            logger.info("Full data migration completed successfully")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
    
    def migrate_countries(self) -> None:
        """Extract unique countries and populate Country table."""
        logger.info("Migrating countries...")
        
        # Extract country data from Salesforce
        countries = self.sf_extractor.get_countries()
        
        with get_db_connection() as conn:
            inserted_count = 0
            for country_record in countries:
                country_name = country_record.get('Key__c')
                if country_name:
                    success = self._insert_country(conn, country_name)
                    if success:
                        inserted_count += 1
                        logger.debug(f"Inserted country: {country_name}")
            
            conn.commit()
            logger.info(f"Countries migration completed - inserted {inserted_count} countries")
    
    def migrate_foreign_credentials(self) -> None:
        """Extract and load Foreign Credential data."""
        logger.info("Migrating foreign credentials...")
        
        # Extract foreign credential data from Salesforce
        credentials = self.sf_extractor.get_foreign_credentials()
        
        with get_db_connection() as conn:
            inserted_count = 0
            skipped_count = 0
            
            for cred_record in credentials:
                country_name = cred_record.get('Key__c')
                foreign_credential = cred_record.get('Value_1__c')
                english_credential = cred_record.get('Value_2__c')
                additional_info = cred_record.get('Value_3__c')
                
                if not country_name:
                    skipped_count += 1
                    continue
                
                # Check if country exists
                if not self._country_exists(conn, country_name):
                    logger.warning(f"Country not found for foreign credential: {country_name}")
                    skipped_count += 1
                    continue
                
                # Insert foreign credential with UUID
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO foreign_credential 
                        (credential_uuid, country_name, foreign_credential, english_credential, additional_info)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        str(uuid.uuid4()),
                        country_name,
                        clean_string(foreign_credential),
                        clean_string(english_credential),
                        clean_string(additional_info)
                    ))
                    inserted_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to insert foreign credential for {country_name}: {e}")
                    skipped_count += 1
            
            conn.commit()
            logger.info(f"Foreign credentials migration completed - inserted {inserted_count}, skipped {skipped_count}")
    
    def migrate_institutions(self) -> None:
        """Extract and load Institution data."""
        logger.info("Migrating institutions...")
        
        # Extract institution data from Salesforce
        institutions = self.sf_extractor.get_institutions()
        
        with get_db_connection() as conn:
            inserted_count = 0
            skipped_count = 0
            
            for inst_record in institutions:
                country_name = inst_record.get('Key__c')
                institution_name = inst_record.get('Value_1__c')
                institution_english_name = inst_record.get('Value_2__c')
                institution_history = inst_record.get('Value_3__c')
                accreditation_status = inst_record.get('Value_4__c')
                
                if not country_name:
                    skipped_count += 1
                    continue
                
                # Check if country exists
                if not self._country_exists(conn, country_name):
                    logger.warning(f"Country not found for institution: {country_name}")
                    skipped_count += 1
                    continue
                
                # Insert institution with UUID
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO institution 
                        (institution_uuid, country_name, institution_name, institution_english_name, institution_history, accreditation_status)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        str(uuid.uuid4()),
                        country_name,
                        clean_string(institution_name),
                        clean_string(institution_english_name),
                        clean_string(institution_history),
                        clean_string(accreditation_status)
                    ))
                    inserted_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to insert institution for {country_name}: {e}")
                    skipped_count += 1
            
            conn.commit()
            logger.info(f"Institutions migration completed - inserted {inserted_count}, skipped {skipped_count}")
    
    def migrate_program_lengths(self) -> None:
        """Extract and load Program Length data."""
        logger.info("Migrating program lengths...")
        
        # Extract program length data from Salesforce
        programs = self.sf_extractor.get_program_lengths()
        
        with get_db_connection() as conn:
            inserted_count = 0
            skipped_count = 0
            
            for prog_record in programs:
                country_name = prog_record.get('Key__c')
                program_length = prog_record.get('Value_1__c')
                
                if not country_name:
                    skipped_count += 1
                    continue
                
                # Check if country exists
                if not self._country_exists(conn, country_name):
                    logger.warning(f"Country not found for program length: {country_name}")
                    skipped_count += 1
                    continue
                
                # Insert program length with UUID
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO program_length (program_length_uuid, country_name, program_length)
                        VALUES (?, ?, ?)
                    """, (
                        str(uuid.uuid4()),
                        country_name,
                        clean_string(program_length)
                    ))
                    inserted_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to insert program length for {country_name}: {e}")
                    skipped_count += 1
            
            conn.commit()
            logger.info(f"Program lengths migration completed - inserted {inserted_count}, skipped {skipped_count}")
    
    def migrate_grade_scales(self) -> None:
        """Extract and load Grade Scale data."""
        logger.info("Migrating grade scales...")
        
        # Extract grade scale data from Salesforce
        scales = self.sf_extractor.get_grade_scales()
        
        with get_db_connection() as conn:
            inserted_count = 0
            skipped_count = 0
            
            for scale_record in scales:
                country_name = scale_record.get('Key__c')
                grade_scale = scale_record.get('Value_1__c')
                bifurcation_setup = scale_record.get('Value_2__c')
                grade_notes = scale_record.get('Value_3__c')
                conversion_factor = scale_record.get('Value_5__c')
                
                if not country_name:
                    skipped_count += 1
                    continue
                
                # Check if country exists
                if not self._country_exists(conn, country_name):
                    logger.warning(f"Country not found for grade scale: {country_name}")
                    skipped_count += 1
                    continue
                
                # Insert grade scale with UUID
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO grade_scale 
                        (grade_scale_uuid, country_name, grade_scale, bifurcation_setup, grade_notes, conversion_factor)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        str(uuid.uuid4()),
                        country_name,
                        clean_string(grade_scale),
                        clean_string(bifurcation_setup),
                        clean_string(grade_notes),
                        clean_string(conversion_factor)
                    ))
                    inserted_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to insert grade scale for {country_name}: {e}")
                    skipped_count += 1
            
            conn.commit()
            logger.info(f"Grade scales migration completed - inserted {inserted_count}, skipped {skipped_count}")
    
    def migrate_us_equivalencies(self) -> None:
        """Extract and load US Equivalency data."""
        logger.info("Migrating US equivalencies...")
        
        # Extract US equivalency data from Salesforce
        equivalencies = self.sf_extractor.get_us_equivalencies()
        
        with get_db_connection() as conn:
            inserted_count = 0
            skipped_count = 0
            
            for equiv_record in equivalencies:
                overall_equivalency = equiv_record.get('Key__c')
                equivalency_description = equiv_record.get('Value_1__c')
                
                if not overall_equivalency:
                    skipped_count += 1
                    continue
                
                # Insert US equivalency with UUID (standalone table)
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO us_equivalency (equivalency_uuid, overall_equivalency, equivalency_description)
                        VALUES (?, ?, ?)
                    """, (
                        str(uuid.uuid4()),
                        clean_string(overall_equivalency),
                        clean_string(equivalency_description)
                    ))
                    inserted_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to insert US equivalency {overall_equivalency}: {e}")
                    skipped_count += 1
            
            conn.commit()
            logger.info(f"US equivalencies migration completed - inserted {inserted_count}, skipped {skipped_count}")
    
    def migrate_notes(self) -> None:
        """Extract and load Notes data."""
        logger.info("Migrating notes...")
        
        # Extract notes data from Salesforce
        notes = self.sf_extractor.get_notes()
        
        with get_db_connection() as conn:
            inserted_count = 0
            skipped_count = 0
            
            for note_record in notes:
                note_content = note_record.get('Key__c')
                
                if not note_content:
                    skipped_count += 1
                    continue
                
                # Insert note with UUID (standalone table)
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO notes (note_uuid, note_content)
                        VALUES (?, ?)
                    """, (
                        str(uuid.uuid4()),
                        clean_string(note_content)
                    ))
                    inserted_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to insert note: {e}")
                    skipped_count += 1
            
            conn.commit()
            logger.info(f"Notes migration completed - inserted {inserted_count}, skipped {skipped_count}")
    
    def _insert_country(self, conn: sqlite3.Connection, country_name: str) -> bool:
        """
        Insert a country using country_name as natural key.
        
        Args:
            conn: Database connection
            country_name: Name of the country
            
        Returns:
            bool: True if inserted successfully, False if already exists or invalid
        """
        # Clean the country name
        cleaned_name = clean_string(country_name)
        if not cleaned_name or not validate_country_name(cleaned_name):
            logger.warning(f"Invalid country name: {country_name}")
            return False
        
        # Check if country already exists
        if self._country_exists(conn, cleaned_name):
            return False  # Already exists
        
        # Insert new country
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO country (country_name) VALUES (?)",
                (cleaned_name,)
            )
            logger.debug(f"Inserted new country: {cleaned_name}")
            return True
            
        except sqlite3.IntegrityError:
            # Handle race condition where country was inserted by another process
            logger.debug(f"Country already exists during insert: {cleaned_name}")
            return False
    
    def _country_exists(self, conn: sqlite3.Connection, country_name: str) -> bool:
        """
        Check if a country exists in the database.
        
        Args:
            conn: Database connection
            country_name: Name of the country
            
        Returns:
            bool: True if country exists, False otherwise
        """
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM country WHERE country_name = ?", (country_name,))
        return cursor.fetchone() is not None