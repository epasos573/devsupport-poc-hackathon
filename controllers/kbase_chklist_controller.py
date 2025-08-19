import logging
from dotenv import load_dotenv
import os

from utils.boto3_utils import SSM
from utils.zendesk_utils import ZendeskClient

# Load env variables
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from utils.openai_utils import OpenAiClient


class KbaseChkListController:
    def __init__(self) -> None:
        # Controller-specific logger
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("KbaseChkListController initialized.")






    def process_openai_request(self):
        """Function to send the context and prompt to OpenAI"""
        self.logger.info("KbaseChkListController::process_openai_request")

        # Initialize connection to OpenAI platform
        openai_client = OpenAiClient()

        # Note: Modify the CONTEXT and PROMPT parameters to be used in the PoC
        data_context = "You are a web developer and you need to see the benefits of using DAM solutions"
        data_prompt  = "Can you provide the summary of Cloudinary as DAM service provider"
        openai_response_data = openai_client.send_prompt(
                context=data_context,
                prompt=data_prompt
            )        
        
        return {
            "OpenAI-Response": openai_response_data
        }




    def process_zendesk_request(self):
        """Function to request Zendesk processing"""
        self.logger.info("KbaseChkListController::process_zendesk_request")

        # Initialize connection to Zendesk platform
        zendesk_config = {
            'zd_url': SSM.get_secret('zendesk_client_url'),
            'zd_email': SSM.get_secret('zendesk_client_email'),
            'zd_api_token': SSM.get_secret('zendesk_client_api_token'),
        }

        # Instantiate the ZendeskClient client
        zendesk_api_client = ZendeskClient(**zendesk_config)

        # Fetch ticket properties from Zendesk API
        # Use the ticket to be used of the PoC
        ticket_id_ref = "333361"
        ticket_properties = zendesk_api_client.ticket_show(ticket_id=ticket_id_ref)
        
        return {
            "Zendesk-Response": ticket_properties
        }

    

