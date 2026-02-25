import operator 
from typing import Annotated, List, Dict, Optional, Any, TypedDict
 
#Define the schema for a single compliance result
#errror report structure
class ComplianceIssue(TypedDict):
    category: str
    description: str
    severity: str
    timestamp: Optional[str]
    
#define the global graph state
class VideoAuditState(TypedDict):
    """_summary_
    Defines the data schema for langgraph execution content
    Main container: holds all the information about the audit 
    right from the initial URL to the final report
    
    Args:
        TypedDict (_type_): _description_
    """
    
    video_url: str
    video_id: str
    
    #ingestion and extraction data
    video_path: Optional[str]
    video_metadata: Dict[str, Any]
    transcript: Optional[str]
    ocr_text: List[str]
    
    #analysis output
    compliance_results: Annotated[List[ComplianceIssue], operator.add]
    
    #final deliverables
    final_status: str #PASS | FAIL
    final_report: str #Markdown format
    
    #system observability 
    #list of system level crashes
    errors: Annotated[List[str], operator.add]