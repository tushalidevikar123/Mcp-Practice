# MCP Practice

A small Python MCP server for practicing tool discovery and use. It provides six tools: `echo`, `add`, `list_project_files`, `search_project_files`, `read_project_file`, and `write_project_file`.

File tools are confined to the directory containing `server.py`. They skip common generated directories, `.env` files, files with `secret` or `credential` in their names, and private-key files. Read and write content is limited to 200 KB. Writes create new files by default; replacing an existing file requires `overwrite=true`.

## Requirements

- Windows and PowerShell
- Python 3.10 or newer, available as `py` (the Windows Python Launcher)
- VS Code with GitHub Copilot Chat for the prompt walkthrough

## Create the environment

Open the repository folder (`Mcp-Practice`) in VS Code. In its integrated PowerShell terminal, run these commands from the folder containing `server.py`:

```powershell
py --version
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install "mcp[cli]>=1.9,<2"
```

If PowerShell blocks activation, either allow activation for this terminal with `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and activate again, or skip activation and use `\.venv\Scripts\python.exe` in place of `python` in the remaining commands. If `py` is not recognized, install Python 3.10 or newer and enable the Python Launcher.

Check that the SDK imports and run the automated test:

```powershell
python -c "import mcp; print('MCP SDK is installed')"
python -m unittest -v
```

The test starts the server over stdio, checks that all six tools are discoverable, exercises each tool, and verifies file access restrictions and overwrite behavior. It removes the temporary file it creates when the test finishes.

## Connect from VS Code

Create `.vscode/mcp.json` in the repository and add this configuration:

```json
{
  "servers": {
    "mcp-practice": {
      "type": "stdio",
      "command": "${workspaceFolder}/.venv/Scripts/python.exe",
      "args": ["${workspaceFolder}/server.py"]
    }
  }
}
```

Save the file. In VS Code, open the MCP server controls from the Command Palette (`MCP: List Servers`), select `mcp-practice`, and start it. VS Code launches the process; do not start `server.py` in a separate terminal for this stdio connection. Open Copilot Chat, choose **Agent** mode, and allow the MCP tools if VS Code asks for approval.

## Try prompts in Agent mode

Ask the agent to use the server tools explicitly, then approve the proposed tool call when prompted:

| Tool | Example prompt |
| --- | --- |
| `echo` | `Use the echo tool with the message "hello MCP".` |
| `add` | `Use the add tool to calculate 12 + 8.` |
| `list_project_files` | `Use list_project_files to show the files in the project root.` |
| `search_project_files` | `Use search_project_files to find "FastMCP" in Python files.` |
| `read_project_file` | `Use read_project_file to read README.md.` |
| `write_project_file` | `Use write_project_file to create prompt-check.txt with the text "MCP write succeeded".` |

For an end-to-end check, paste this prompt into Copilot Chat in **Agent** mode:

```text
Test the mcp-practice server using its MCP tools only. Do not edit files directly.

1. Call echo with "hello MCP".
2. Call add with 12 and 8.
3. List files in the project root.
4. Search Python files for "FastMCP".
5. Read README.md.
6. Try reading ../README.md and confirm the server rejects the path.
7. Create a new file named mcp-prompt-test.txt with the content "MCP write succeeded". Read it back.
8. Try writing different content to that same file without overwrite; confirm it is refused. Then set overwrite=true, write "Updated", and read it back.

Report each result, including any rejected calls. Do not overwrite any other existing file.
```

This test leaves `mcp-prompt-test.txt` in the project. Remove it manually when finished. If that filename already exists, use a fresh filename in the prompt.

Confirm the write by asking `Use read_project_file to read prompt-check.txt.` The created file is in the repository and can be removed when finished. To check the overwrite safeguard, ask the agent to write to `prompt-check.txt` again with different content without requesting overwrite; the tool should refuse. To replace it, explicitly ask for overwrite, for example: `Use write_project_file to replace prompt-check.txt with "Updated" and set overwrite to true.`

For a quick safety check, try `Use read_project_file to read ../README.md.` The tool should reject paths outside the project directory. The server also excludes `.env` and other sensitive paths from project-file operations.

## Run the server manually (optional)

To run the stdio server through the MCP Inspector, use:

```powershell
python -m mcp dev server.py
```

To run the optional Streamable HTTP transport instead:

```powershell
python server.py --transport streamable-http
```

Connect an HTTP-capable MCP client to `http://127.0.0.1:8000/mcp` and keep the terminal open. The server binds to localhost by default. Do not expose it publicly without appropriate authentication and network access controls.