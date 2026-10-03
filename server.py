from pathlib import Path

from mcp.server import MCPServer


# ローカルのファイル操作Toolを公開するMCP Server
mcp = MCPServer("MCP File Tool Server")


@mcp.tool()
def read_text_file(path: str) -> str:
    """指定したテキストファイルの内容を読み込みます。"""
    return Path(path).read_text(encoding="utf-8")


@mcp.tool()
def list_files(path: str) -> list[str]:
    """指定したフォルダ直下のファイル一覧を取得します。"""
    folder = Path(path)
    return [p.name for p in folder.iterdir() if p.is_file()]


@mcp.tool()
def get_file_info(path: str) -> dict:
    """指定したファイルの名前・拡張子・サイズ・存在有無を取得します。"""
    file_path = Path(path)

    if not file_path.exists():
        return {
            "name": file_path.name,
            "exists": False,
        }

    return {
        "name": file_path.name,
        "suffix": file_path.suffix,
        "size": file_path.stat().st_size,
        "exists": True,
    }


@mcp.tool()
def search_folder_text(folder_path: str, keyword: str) -> dict[str, list[str]]:
    """指定したフォルダ直下のtxtファイルから、キーワードを含む行を検索します。"""
    results: dict[str, list[str]] = {}

    for path in Path(folder_path).glob("*.txt"):
        lines = path.read_text(encoding="utf-8").splitlines()
        matched = [line for line in lines if keyword in line]

        if matched:
            results[path.name] = matched

    return results


@mcp.tool()
def count_keyword(folder_path: str, keyword: str) -> dict[str, int]:
    """指定したフォルダ直下のtxtファイルごとに、キーワードの出現回数を数えます。"""
    results: dict[str, int] = {}

    for path in Path(folder_path).glob("*.txt"):
        text = path.read_text(encoding="utf-8")
        count = text.count(keyword)

        if count > 0:
            results[path.name] = count

    return results
