"""
Salesforce connection and authentication management.

Provides Salesforce client setup using credentials from config.
"""

import logging
from typing import Optional
from simple_salesforce import Salesforce
import config


logger = logging.getLogger(__name__)


class SalesforceClient:
    """Manages Salesforce connection and authentication."""
    
    def __init__(self):
        """Initialize Salesforce client."""
        self.sf: Optional[Salesforce] = None
        self._validate_credentials()
    
    def _validate_credentials(self) -> None:
        """Validate that all required Salesforce credentials are available."""
        try:
            config.validate_salesforce_creds()
            logger.debug("Salesforce credentials validated")
        except Exception as e:
            logger.error(f"Salesforce credential validation failed: {e}")
            raise
    
    def connect(self) -> Salesforce:
        """
        Establish connection to Salesforce.
        
        Returns:
            Salesforce: Authenticated Salesforce client instance
            
        Raises:
            Exception: If connection fails
        """
        if self.sf is not None:
            logger.debug("Using existing Salesforce connection")
            return self.sf
        
        try:
            logger.info("Connecting to Salesforce...")
            
            self.sf = Salesforce(
                username=config.SF_USERNAME,
                password=config.SF_PASSWORD,
                security_token=config.SF_SECURITY_TOKEN,
                consumer_key=config.SF_CLIENT_ID,
                consumer_secret=config.SF_CLIENT_SECRET,
                domain=config.SF_DOMAIN
            )
            
            logger.info("Successfully connected to Salesforce")
            return self.sf
            
        except Exception as e:
            logger.error(f"Failed to connect to Salesforce: {e}")
            raise
    
    def disconnect(self) -> None:
        """Close the Salesforce connection."""
        if self.sf is not None:
            # simple-salesforce doesn't have explicit disconnect
            self.sf = None
            logger.info("Salesforce connection closed")
    
    def test_connection(self) -> bool:
        """
        Test the Salesforce connection.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            sf = self.connect()
            # Simple query to test connection
            sf.query("SELECT Id FROM User LIMIT 1")
            logger.info("Salesforce connection test successful")
            return True
        except Exception as e:
            logger.error(f"Salesforce connection test failed: {e}")
            return False


def get_salesforce_client() -> SalesforceClient:
    """
    Factory function to get a configured Salesforce client.
    
    Returns:
        SalesforceClient: Configured client instance
    """
    return SalesforceClient()