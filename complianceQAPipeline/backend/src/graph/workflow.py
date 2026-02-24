'''
This module defines the DAG: Directed Acyclic Graph that orchestrates the video compliance
audit process.
it connects the nodes using the stategraph from langgraph
'''

from langgraph.graph import StateGraph,END
from backend.src.graph.state import VideoAuditState
from backend.src.graph.nodes import (
    index_video_node,
    audio_content_node
)

def create_graph():
    '''
    Constructs and compiles the langgraph workflow
    
    Returns:
    Compiled Graph: runnable graph object for execution 
    '''
    
    #initialize the graph with stateschema
    workflow = StateGraph(VideoAuditState)
    #add nodes
    workflow.add_node("indexer", index_video_node)
    workflow.add_node("auditor", audio_content_node)
    #define the entry point: indexer
    workflow.set_entry_point("indexer")
    #define the edges
    workflow.add_edge("indexer","auditor")
    workflow.add_edge("auditor", END)
    
    app = workflow.compile()
    
    return app

app = create_graph()