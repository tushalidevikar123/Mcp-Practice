"""A small MCP server that works with local and remote MCP clients."""

import argparse
from pathlib import Path

from mcp.server.fastmcp import FastMCP


mcp = FastMCP("mcp-practice")
PROJECT_ROOT: Path = Path(__file__).resolve().parent
IGNORED_DIRECTORIES: frozenset[str] = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
        "venv",
    }
)
SENSITIVE_SUFFIXES: frozenset[str] = frozenset({".key", ".pem", ".p12", ".pfx"})
MAX_FILE_SIZE: int = 200_000
MAX_RESULTS: int = 200


def _is_excluded(relative_path: Path) -> bool:
    if any(part.casefold() in IGNORED_DIRECTORIES for part in relative_path.parts):
        return True

    name = relative_path.name.casefold()
    return (
        name == ".env"
        or name.startswith(".env.")
        or "secret" in name
        or "credential" in name
        or relative_path.suffix.casefold() in SENSITIVE_SUFFIXES
    )


def _resolve_project_path(path: str) -> Path:
    resolved_path = (PROJECT_ROOT / path).resolve()
    try:
        relative_path = resolved_path.relative_to(PROJECT_ROOT)
    except ValueError as error:
        raise ValueError("Path must stay inside the project directory.") from error

    if _is_excluded(relative_path):
        raise ValueError("This path is excluded from project access.")
    return resolved_path


def _project_files(directory: Path) -> list[Path]:
    files: list[Path] = []
    for candidate in directory.rglob("*"):
        if not candidate.is_file():
            continue
        try:
            relative_path = candidate.resolve().relative_to(PROJECT_ROOT)
        except ValueError:
            continue
        if not _is_excluded(relative_path):
            files.append(PROJECT_ROOT / relative_path)
    return sorted(files)


@mcp.tool()
def echo(message: str) -> str:
    """Return the supplied message."""
    return message


@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


@mcp.tool()
def list_project_files(directory: str = ".") -> str:
    """List readable files under a project directory, relative to the project root."""
    target_directory = _resolve_project_path(directory)
    if not target_directory.is_dir():
        raise ValueError("The requested project path is not a directory.")

    files = _project_files(target_directory)
    displayed_files = files[:MAX_RESULTS]
    output = [path.relative_to(PROJECT_ROOT).as_posix() for path in displayed_files]
    if len(files) > MAX_RESULTS:
        output.append(f"... {len(files) - MAX_RESULTS} more files omitted")
    return "\n".join(output) if output else "No project files found."


@mcp.tool()
def search_project_files(query: str, file_pattern: str = "*.py") -> str:
    """Search project text files for a case-insensitive query."""
    if not query.strip():
        raise ValueError("Search query cannot be empty.")

    matches: list[str] = []
    normalized_query = query.casefold()
    for path in _project_files(PROJECT_ROOT):
        if not path.match(file_pattern) or path.stat().st_size > MAX_FILE_SIZE:
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        relative_path = path.relative_to(PROJECT_ROOT).as_posix()
        for line_number, line in enumerate(lines, start=1):
            if normalized_query in line.casefold():
                matches.append(f"{relative_path}:{line_number}: {line[:300]}")
                if len(matches) >= MAX_RESULTS:
                    return "\n".join(matches)
    return "\n".join(matches) if matches else "No matches found."


@mcp.tool()
def read_project_file(path: str) -> str:
    """Read a UTF-8 text file inside the project directory."""
    target_path = _resolve_project_path(path)
    if not target_path.is_file():
        raise ValueError("The requested project file does not exist.")
    if target_path.stat().st_size > MAX_FILE_SIZE:
        raise ValueError(f"File exceeds the {MAX_FILE_SIZE}-byte read limit.")
    try:
        return target_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("The requested file is not UTF-8 text.") from error


@mcp.tool()
def write_project_file(path: str, content: str, overwrite: bool = False) -> str:
    """Create a UTF-8 project file; replacing an existing file requires overwrite=true."""
    target_path = _resolve_project_path(path)
    if len(content.encode("utf-8")) > MAX_FILE_SIZE:
        raise ValueError(f"Content exceeds the {MAX_FILE_SIZE}-byte write limit.")
    if not target_path.parent.is_dir():
        raise ValueError("The parent directory must already exist inside the project.")

    existed = target_path.exists()
    try:
        with target_path.open("w" if overwrite else "x", encoding="utf-8") as output_file:
            output_file.write(content)
    except FileExistsError as error:
        raise ValueError("File already exists; set overwrite=true to replace it.") from error

    action = "Updated" if existed else "Created"
    return f"{action} {target_path.relative_to(PROJECT_ROOT).as_posix()}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the MCP Practice server.")
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http"),
        default="stdio",
        help="Connection type used by the MCP client (default: stdio).",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host for Streamable HTTP (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for Streamable HTTP (default: 8000).",
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run()
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()