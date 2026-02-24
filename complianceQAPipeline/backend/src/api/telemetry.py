import os
import logging
from azure.monitor.opentelemetry import configure_azure_monitor
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger("brand-gaurdian.-telemetry")

def setup_telemetry():
    '''
    Initializes Azure Monitor OpenTelemetry
    TRACKS: HTTP requests, database queries, errors, performance metrics.
    Sends this data to azure monitor
    
    it auto captures every API requests
    No need to manually log each entry
    '''
    
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    #check if configured
    if not connection_string:
        logger.warning("No instrument key found. Telemetry is DISABLED.")
        return
    #Configure the azure monitor
    try:
        configure_azure_monitor( 
            connection_string=connection_string,
            logger_name= "brand-gaurdian-tracer"
        )
        logger.info("Azure Monitor Tracking Enabled and Connected")
    except Exception as e:
        logger.error(f"Failed to initialize Azure Monitor: {e}")