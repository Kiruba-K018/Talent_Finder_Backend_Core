from langgraph.graph import END, StateGraph

from src.control.agents.scoring_agent.nodes import (
    calculate_base_scores_node,
    continue_processing,
    create_shortlist_node,
    load_candidates_node,
    process_candidate_node,
    save_scores_node,
    save_shortlist_to_db,
    similarity_search_and_rank_node,
)
from src.control.agents.scoring_agent.state import ScoringState


def create_scoring_graph():
    graph = StateGraph(ScoringState)

    graph.add_node("load_candidates", load_candidates_node)
    graph.add_node("calculate_base_scores", calculate_base_scores_node)
    graph.add_node("similarity_search_and_rank", similarity_search_and_rank_node)
    graph.add_node("process_candidate", process_candidate_node)
    graph.add_node("create_shortlist", create_shortlist_node)
    graph.add_node("save_scores", save_scores_node)
    graph.add_node("save_shortlist_to_db", save_shortlist_to_db)

    graph.set_entry_point("load_candidates")

    graph.add_edge("load_candidates", "calculate_base_scores")
    graph.add_edge("calculate_base_scores", "similarity_search_and_rank")
    graph.add_edge("similarity_search_and_rank", "process_candidate")
    graph.add_conditional_edges(
        "process_candidate",
        continue_processing,
        {"process_candidate": "process_candidate", END: "create_shortlist"},
    )
    graph.add_edge("create_shortlist", "save_scores")
    graph.add_edge("save_scores", "save_shortlist_to_db")
    graph.add_edge("save_shortlist_to_db", END)

    return graph.compile()


graph = create_scoring_graph()
