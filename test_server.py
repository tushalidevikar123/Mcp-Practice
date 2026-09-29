import asyncio
import sys
import unittest
from pathlib import Path
from uuid import uuid4

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class StdioServerTests(unittest.TestCase):
    def test_tools_over_stdio(self) -> None:
        asyncio.run(self._check_tools())

    async def _check_tools(self) -> None:
        params = StdioServerParameters(
            command=sys.executable,
            args=["server.py"],
            cwd=str(Path(__file__).parent),
        )
        write_test_path = f".mcp-write-test-{uuid4().hex}.txt"
        try:
            async with stdio_client(params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    self.assertEqual(
                        {tool.name for tool in tools.tools},
                        {
                            "add",
                            "echo",
                            "list_project_files",
                            "read_project_file",
                            "search_project_files",
                            "write_project_file",
                        },
                    )

                    result = await session.call_tool("echo", {"message": "hello MCP"})
                    self.assertEqual(result.content[0].text, "hello MCP")

                    result = await session.call_tool("add", {"a": 12, "b": 8})
                    self.assertEqual(result.structuredContent["result"], 20)

                    result = await session.call_tool("list_project_files", {"directory": "."})
                    self.assertIn("server.py", result.content[0].text)
                    self.assertNotIn(".venv", result.content[0].text)

                    result = await session.call_tool(
                        "search_project_files", {"query": "FastMCP"}
                    )
                    self.assertIn("server.py:", result.content[0].text)

                    result = await session.call_tool("read_project_file", {"path": "server.py"})
                    self.assertIn("FastMCP", result.content[0].text)

                    result = await session.call_tool(
                        "read_project_file", {"path": "../README.md"}
                    )
                    self.assertTrue(result.isError)

                    result = await session.call_tool("read_project_file", {"path": ".env"})
                    self.assertTrue(result.isError)

                    result = await session.call_tool(
                        "write_project_file",
                        {"path": write_test_path, "content": "first version"},
                    )
                    self.assertIn("Created", result.content[0].text)

                    result = await session.call_tool(
                        "write_project_file",
                        {"path": write_test_path, "content": "blocked overwrite"},
                    )
                    self.assertTrue(result.isError)

                    result = await session.call_tool(
                        "read_project_file", {"path": write_test_path}
                    )
                    self.assertEqual(result.content[0].text, "first version")

                    result = await session.call_tool(
                        "write_project_file",
                        {
                            "path": write_test_path,
                            "content": "updated version",
                            "overwrite": True,
                        },
                    )
                    self.assertIn("Updated", result.content[0].text)

                    result = await session.call_tool(
                        "read_project_file", {"path": write_test_path}
                    )
                    self.assertEqual(result.content[0].text, "updated version")

                    result = await session.call_tool(
                        "write_project_file",
                        {"path": "../outside.txt", "content": "blocked", "overwrite": True},
                    )
                    self.assertTrue(result.isError)
        finally:
            (Path(__file__).parent / write_test_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()