import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.graph import AgentState, graph, build_graph

class TestGraphOffline(unittest.TestCase):
    @patch('agent.graph.llm')
    @patch('agent.graph.execute_sql')
    @patch('agent.graph.render_schema')
    def test_graph_success_first_try(self, mock_render_schema, mock_execute_sql, mock_llm):
        # Setup mocks
        mock_render_schema.return_value = "Mock Schema"
        
        # Mock LLM calls:
        # First call is generate_sql, return simple query
        # Second call is verify, return JSON ok=True
        mock_response_gen = MagicMock()
        mock_response_gen.content = "```sql\nSELECT * FROM dummy;\n```"
        
        mock_response_ver = MagicMock()
        mock_response_ver.content = '{"ok": true, "issue": ""}'
        
        mock_llm.return_value.invoke.side_effect = [mock_response_gen, mock_response_ver]
        
        # Mock SQL execution
        from agent.execution import ExecutionResult
        mock_execute_result = ExecutionResult(ok=True, rows=[(1,)], columns=["col"], row_count=1)
        mock_execute_sql.return_value = mock_execute_result
        
        # Run graph
        state = AgentState(question="Mock Question", db_id="mock_db")
        result = graph.invoke(state)
        
        # Assertions
        self.assertEqual(result["sql"], "SELECT * FROM dummy;")
        self.assertEqual(result["iteration"], 1)
        self.assertTrue(result["verify_ok"])
        self.assertEqual(result["verify_issue"], "")
        
    @patch('agent.graph.llm')
    @patch('agent.graph.execute_sql')
    @patch('agent.graph.render_schema')
    def test_graph_revision_loop(self, mock_render_schema, mock_execute_sql, mock_llm):
        # Setup mocks
        mock_render_schema.return_value = "Mock Schema"
        
        # Mocks:
        # 1. generate_sql -> SELECT * FROM bad;
        # 2. verify (fails) -> ok=false, issue="table does not exist"
        # 3. revise -> SELECT * FROM good;
        # 4. verify (succeeds) -> ok=true, issue=""
        mock_response_gen = MagicMock(content="SELECT * FROM bad;")
        mock_response_ver1 = MagicMock(content='{"ok": false, "issue": "table bad does not exist"}')
        mock_response_rev = MagicMock(content="SELECT * FROM good;")
        mock_response_ver2 = MagicMock(content='{"ok": true, "issue": ""}')
        
        mock_llm.return_value.invoke.side_effect = [
            mock_response_gen,
            mock_response_ver1,
            mock_response_rev,
            mock_response_ver2
        ]
        
        # Mock SQL execution
        from agent.execution import ExecutionResult
        mock_execute_sql.side_effect = [
            ExecutionResult(ok=False, error="no such table: bad"),
            ExecutionResult(ok=True, rows=[(1,)], columns=["col"], row_count=1)
        ]
        
        state = AgentState(question="Mock Question", db_id="mock_db")
        result = graph.invoke(state)
        
        # Assertions
        self.assertEqual(result["sql"], "SELECT * FROM good;")
        self.assertEqual(result["iteration"], 2)  # 1 generate + 1 revise
        self.assertTrue(result["verify_ok"])
        self.assertEqual(result["verify_issue"], "")

if __name__ == "__main__":
    unittest.main()
