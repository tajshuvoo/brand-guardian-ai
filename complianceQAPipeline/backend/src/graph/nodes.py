import json
import os
import logging
import re
from typing import Dict, Any, List

from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint, HuggingFaceEmbeddings
from langchain_community.vectorstores import AzureSearch
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

from dotenv import load_dotenv


load_dotenv()

#import state schema
from backend.src.graph.state import VideoAuditState, ComplianceIssue
#import service
from backend.src.services.video_indexer import VideoIndexerService

#config logger
logger = logging.getLogger("brand-gaurdian")
logging.basicConfig(level=logging.INFO)

#NODE 1: INDEXER
def index_video_node(state:VideoAuditState) -> Dict[str, Any]:
    """_summary_
        Downloads the youtube video fro the url
        Uploads to the azure video indexer
        extracts the insights
        
    Args:
        state (VideoAuditState): _description_

    Returns:
        Dict[str, Any]: _description_
    """
    
    video_url = state.get("video_url")
    video_id_input = state.get("video_id", "vid_demo")
    
    logger.info(f"-----[Node:Indexer] Processing : {video_url}")
    
    local_filename= "temp_audit_video.mp4 "
    
    try:
        vi_service = VideoIndexerService()
        #download 
        if "youtube.com" in video_url or "youtu.be" in video_url:
            local_path= vi_service.download_youtube_video(video_url, output_path= local_filename)
        else:
            raise Exception("Please provide a valid Youtube URL for this test")
        
        #upload 
        azure_video_id = vi_service.upload_video(local_path, video_name= video_id_input)
        logger.info(f"Upload Success. Azure ID: {azure_video_id}")
        
        #cleanup
        
        if os.path.exists(local_path):
            os.remove(local_path)
        #wait
        
        raw_insights = vi_service.wait_for_processing(azure_video_id)
        #extract
        clean_data = vi_service.extract_data(raw_insights)
        logger.info("---[NODE: Indexer] Extraction Complete ---")
        return clean_data
    
    except Exception as e:
        logger.error(f"Video Indexer Failed : {e} ")
        return {
            "errors":[str(e)],
            "final_status": "FAIL",
            "transcript": "",
            "ocr_text":[]   
        }


#Node 2: Compliance Auditor
def audio_content_node(state: VideoAuditState) -> Dict[str, Any]:
    """_summary_
        Performs Retrieved Augmented Generation to audit the content - brand video
    Args:
        state (VideoAuditState): _description_

    Returns:
        Dict[str, Any]: _description_
    """
    
    logger.info("---[NODE: Auditor] querying the knowledge base and LLM")
    transcript= state.get("transcript", "")
    if not transcript:
        logger.warning("No transcript available. Skipping audit.....")
        return {
            "final_status":"FAIL",
            "final_report": "Audit Skipped because video processing failed (No transcript.)"
        }
    
    #initialize clients
    llm = HuggingFaceEndpoint(
        repo_id="Qwen/Qwen2.5-14B-Instruct",
        temperature=0,
        max_new_tokens=2000,
    )
    llm = ChatHuggingFace(llm=llm)
    
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    vector_store = AzureSearch(
        azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        azure_search_key= os.getenv("AZURE_SEARCH_API_KEY"),
        index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
        embedding_function=embeddings.embed_query
    )
    
    #RAG retrival 
    ocr_text = state.get("ocr_text",[])
    query_text = f"{transcript} {''.join(ocr_text)}"
    docs = vector_store.similarity_search(query_text, k=3)
    retrived_rules = "\n\n".join([doc.page_content for doc in docs])
    
    #
    system_prompt = f"""
                    You are a senior brand compliance auditor.
                    OFFICIAL REGULATORY RULES:
                    {retrived_rules}
                    INSTRUCTIONS:
                    1. Analyze the transcript and OCR text below.
                    2. Identify any violation of the rules.
                    3. Return strictly JSON in the following format:
                    {{
                    "compliance_results": [
                        {{
                            "category": "Claim Validation",
                            "severity": "CRITICAL",
                            "description": "Explanation of the violation..."
                        }}
                    ],
                    "status": "FAIL", 
                    "final_report": "Summary of findings..."
                     }}

                    If no violations are found, set "status" to "PASS" and "compliance_results" to [].
                """
    user_message = f"""
                    VIDEO_METADATA: {state.get('video_metadata',{})}
                    TRANSCRIPT: {transcript}
                    ON SCREEN TEXT (OCR): {ocr_text}
                """
                
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ])
        content = response.content.strip()

        # Remove markdown code fences safely
        if content.startswith("```"):
            content = re.sub(r"^```json", "", content)
            content = re.sub(r"^```", "", content)
            content = re.sub(r"```$", "", content)
            content = content.strip()

        # Extract JSON object safely
        match = re.search(r"\{.*\}", content, re.DOTALL)

        if not match:
            raise ValueError(f"No JSON object found in LLM output:\n{content}")

        json_str = match.group(0)

        audit_data = json.loads(json_str)
        return {
            "compliance_results": audit_data.get("compliance_results", []),
            "final_status": audit_data.get("status", "FAIL"),
            "final_report": audit_data.get("final_report", "No report generated")
        }
    
    except Exception as e:
        logger.error(f"System error in Auditor Node: {str(e)}")
        logger.error(f"Raw LLM response: {response.content if 'response' in locals() else 'None'}")
        return {
            "errors": [str(e)],
            "final_status": "FAIL"
        }