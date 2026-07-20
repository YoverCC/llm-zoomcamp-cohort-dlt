import os
from pathlib import Path
from typing import Optional, List, Dict, Any

import duckdb


def get_input_tokens_for_query(query_text: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get input token counts for all model calls in a trace containing the given query text.
    
    Args:
        query_text: The query text to search for (e.g., "How do I run Ollama locally?")
        db_path: Optional path to the DuckDB file. If not provided, uses the default location.
        
    Returns:
        List of dicts with model call details including input_tokens, output_tokens, timestamp, etc.
    """
    if db_path is None:
        repo_root = Path(__file__).resolve().parent
        db_path = repo_root / ".dlt" / "data" / "dev" / "logfire_pipeline.duckdb"
    
    db_path = str(db_path)
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"DuckDB file not found at {db_path}")
    
    conn = duckdb.connect(db_path)
    try:
        # First, find the trace containing the query
        find_trace_query = f"""
        SELECT DISTINCT trace_id 
        FROM logfire_data.agent_traces 
        WHERE attributes__gen_ai_tool_call_arguments__query ILIKE '%{query_text}%'
        LIMIT 1
        """
        
        trace_result = conn.execute(find_trace_query).fetchall()
        
        if not trace_result:
            return []
        
        trace_id = trace_result[0][0]
        
        # Get all model calls in that trace with token usage
        get_calls_query = f"""
        SELECT 
            span_name,
            message,
            attributes__gen_ai_usage_input_tokens AS input_tokens,
            attributes__gen_ai_usage_output_tokens AS output_tokens,
            attributes__gen_ai_aggregated_usage_input_tokens AS aggregated_input_tokens,
            attributes__gen_ai_aggregated_usage_output_tokens AS aggregated_output_tokens,
            attributes__gen_ai_operation_name AS operation_name,
            start_timestamp,
            attributes__gen_ai_tool_call_arguments__query AS tool_query
        FROM logfire_data.agent_traces
        WHERE trace_id = '{trace_id}'
            AND span_name = 'chat gpt-5.4-mini'
        ORDER BY start_timestamp ASC
        """
        
        result = conn.execute(get_calls_query).fetchall()
        
        # Format as list of dicts
        model_calls = []
        for row in result:
            call = {
                "span_name": row[0],
                "message": row[1],
                "input_tokens": row[2],
                "output_tokens": row[3],
                "aggregated_input_tokens": row[4],
                "aggregated_output_tokens": row[5],
                "operation_name": row[6],
                "start_timestamp": row[7],
                "tool_query": row[8],
            }
            model_calls.append(call)
        
        return model_calls
    
    finally:
        conn.close()


if __name__ == "__main__":
    # Example usage
    query = "run Ollama"
    print(f"Getting input tokens for query: '{query}'\n")
    
    try:
        results = get_input_tokens_for_query(query)
        
        if not results:
            print(f"No records found for query: {query}")
        else:
            print(f"Found {len(results)} model calls:\n")
            for i, call in enumerate(results, 1):
                print(f"Call {i}:")
                if call["input_tokens"] is not None:
                    print(f"  input_tokens: {call['input_tokens']}")
                    print(f"  output_tokens: {call['output_tokens']}")
                else:
                    print(f"  input_tokens: None (no token data)")
                print(f"  operation: {call['operation_name']}")
                print(f"  timestamp: {call['start_timestamp']}")
                print()
    
    except FileNotFoundError as e:
        print(f"Error: {e}")
