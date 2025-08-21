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





    def get_ticket_internal_notes(self, ticket_id):
        # Initialize connection to Zendesk platform
        zendesk_config = {
            'zd_url': SSM.get_secret('zendesk_client_url'),
            'zd_email': SSM.get_secret('zendesk_client_email'),
            'zd_api_token': SSM.get_secret('zendesk_client_api_token'),
        }

        # Instantiate the ZendeskClient client
        zendesk_api_client = ZendeskClient(**zendesk_config)

        # Fetch ticket properties from Zendesk API
        ticket_all_comments = zendesk_api_client.ticket_list_comments(ticket_id=ticket_id)

        internal_note_data = ticket_all_comments["comments"][3]
        
        return internal_note_data
        

    def get_confluence_data(self, title):

        # ToDo: To be extracted from Confluence Page by title
        confluence_data = "TODO - feature to be implemented here..."

        return confluence_data


    def get_openai_analysis(self, proposed_updates_and_changes, confluence_data, zendesk_kb_data = "",  zendesk_macro_data = ""):
        """Function to send the context and prompt to OpenAI"""

        # Initialize connection to OpenAI platform
        openai_client = OpenAiClient()

        # Note: Modify the CONTEXT and PROMPT parameters to be used in the PoC
        data_context = """
            You are dev support team and you need to identify if there are some changes needed for the different information sources:
            **confluence_data**: {confluence_data}
            **zendesk_kb_data**: {zendesk_kb_data}
            **zendesk_macro_data**: {zendesk_macro_data}
        """

        data_prompt  = "You can check the proposed changes: {proposed_updates_and_changes}"

        openai_response_data = openai_client.send_prompt(
                context=data_context,
                prompt=data_prompt
            )        
        
        return openai_response_data


    def create_confluence_page(self, new_confluence_data):

        # Update the confluence Page here

        # NotYetImplemented

        # Add the code here

        return True





    def process_demo_workflow(self):
        """Function to demo the use cases as detailed for hackathon"""
        self.logger.info("KbaseChkListController::process_demo_workflow")

        ##############################
        # Get the Ticket Internal Note

        # Use the ticket to be used of the PoC
        ticket_id_ref = "333361"
        internal_notes = self.get_ticket_internal_notes(ticket_id=ticket_id_ref)
        internal_notes_body = internal_notes['body']

        
        # We can use hard-coded for the PoC (they can be extracted from internal_notes_body):
        confluence_kb_title     = "Invalidation after deletion (getting 404 error)"
        zendesk_kb_title        = "CDN Invalidations: URL conventions invalidated for removed or replaced assets"
        zendesk_macro_title     = "Delivery::CDN Invalidation::Invalidation settings and switching between URL based to Surrogate-key invalidation (partial - fill in blanks)"
        
        proposed_updates_and_changes = "This is just a demo but there might be some information to be updated"




        ##############################
        # Get the Confluence Page based on Title
        confluence_data = self.get_confluence_data(confluence_kb_title)




        ##############################
        # Get Zendesk KB based on title
        # NotYetImplemented



        ##############################
        # Get Zendesk Macro based on title
        # NotYetImplemented



        ##############################
        ### Do the analysis and create new confluence page

        new_confluence_analysis_data = self.get_openai_analysis(proposed_updates_and_changes, confluence_data, zendesk_kb_data = "",  zendesk_macro_data = "")

        self.create_confluence_page(new_confluence_data=new_confluence_analysis_data)

        return {
            "processing": new_confluence_analysis_data
        }

















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
        ticket_properties = zendesk_api_client.ticket_list_comments(ticket_id=ticket_id_ref)
        
        return {
            "Zendesk-Response": ticket_properties
        }

    

