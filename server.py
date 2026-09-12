from pathlib import Path

from mcp.server import MCPServer


mcp = MCPServer("My MCP Server")


@mcp.tool()
def read_text_file(path: str) -> str:
    """指定したテキストファイルの内容を読み込みます。"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@mcp.tool()
def list_files(path: str) -> list[str]:
    """指定したフォルダ内のファイル一覧を取得します。"""
    return [p.name for p in Path(path).iterdir()]


@mcp.tool()
def get_file_info(path: str) -> dict:
    """指定したファイルの基本情報を取得します。"""
    file_path = Path(path)

    if not file_path.exists():
        return {
            "name": file_path.name,
            "exists": False
        }

    return {
        "name": file_path.name,
        "suffix": file_path.suffix,
        "size": file_path.stat().st_size,
        "exists": True
    }


@mcp.tool()
def search_folder_text(
    folder_path: str,
    keyword: str
) -> dict[str, list[str]]:
    """指定したフォルダ内のテキストファイルから、キーワードを含む行を検索します。"""

    results = {}

    for path in Path(folder_path).glob("*.txt"):
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        matched = [
            line.strip()
            for line in lines
            if keyword in line
        ]

        if matched:
            results[path.name] = matched

    return results


@mcp.tool()
def count_keyword(
    folder_path: str,
    keyword: str
) -> dict[str, int]:
    """指定したフォルダ内のテキストファイルごとに、キーワードの出現回数を数えます。"""

    results = {}

    for path in Path(folder_path).glob("*.txt"):
        text = path.read_text(encoding="utf-8")
        count = text.count(keyword)

        if count > 0:
            results[path.name] = count

    return results