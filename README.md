# MCP Multi-Tool Agent

MCP（Model Context Protocol）を利用し、複数のPython関数をToolとして公開し、LLMがユーザーの質問内容に応じて適切なToolを選択・実行する仕組みを実装しました。

## 概要

MCP Server側に複数のToolを登録し、MCP ClientからTool情報を取得します。

取得したTool情報をOpenAIのFunction Calling形式へ変換してLLMへ渡すことで、Client側にToolごとの `if / elif` を固定的に記述せず、LLMが質問内容に応じてToolを選択できる構成としています。

```text
ユーザーの質問
↓
LLMへ質問 + Tool情報を送信
↓
LLMがToolと引数を選択
↓
MCP ClientがToolを実行
↓
Tool実行結果をLLMへ返す
↓
最終回答を生成
```

## 主なTool

```text
read_text_file
→ 指定したテキストファイルを読み込む

list_files
→ フォルダ内のファイル一覧を取得する

get_file_info
→ ファイルの基本情報を取得する

search_folder_text
→ 複数ファイルからキーワードを含む行を検索する

count_keyword
→ ファイルごとにキーワードの出現回数を取得する
```

各ToolはPython関数として実装し、`@mcp.tool()` デコレータによってMCP Toolとして登録しています。

docstringはToolの `description` として利用され、Tool名・description・引数schemaをLLMが参照してToolを選択します。

## MCPを利用する利点

今回の実装では、Server側へ新しいToolを追加した場合でも、Client側にそのTool専用の分岐処理を追加する必要がありません。

```text
ServerへPython関数を追加
↓
@mcp.tool() でTool登録
↓
Clientが list_tools() で取得
↓
LLMへTool情報を渡す
↓
LLMが必要に応じてToolを選択
```

異なる処理をMCP Toolという共通形式で公開し、Client側から統一的に取得・実行できる点を確認しました。

## ファイル構成

```text
mcp-multitool-agent/
├─ 04_MCPを利用した複数Tool連携.ipynb
├─ server.py
├─ client.py
└─ data/
    ├─ AI利用ルール.txt
    ├─ PC申請.txt
    ├─ セキュリティ.txt
    ├─ 有給休暇.txt
    └─ 障害対応.txt
```

- `server.py` : MCP ServerおよびTool定義
- `client.py` : MCP Client、OpenAI API連携、Tool実行
- `data/` : 動作確認用のダミーテキストデータ
- Notebook : MCPの仕組みと実装過程を段階的に解説

## 使用技術

```text
Python 3.12
MCP Python SDK
OpenAI API
Jupyter Notebook
Anaconda
```

## 実行構成

今回の実装では、MCP Client・MCP Server・Toolを同一PC上で動作させています。

Notebookでは処理を段階的に確認し、最終的に `client.py` としてまとめ、Pythonスクリプト単体でも実行できることを確認しました。

```text
python client.py
```

## 実装範囲

今回はMCPの基本的なTool連携を理解することを目的として、1回の質問につき1つのToolを選択するシンプルな構成としています。

今後は、複数Toolの連続実行、エラー処理、リモートMCP Serverとの接続、UIとの連携などへの拡張が可能です。

## Notebook

実装内容・MCP Server / Clientの役割・`async / await / async with`・Tool選択の仕組みなどは、以下のNotebookで詳しく解説しています。

**`04_MCPを利用した複数Tool連携.ipynb`**


## 注意事項

本リポジトリで使用している社内文書は、MCPによるTool連携の動作確認を目的として作成したダミーデータです。

実在する企業・組織の社内文書ではありません。

## 動作確認環境

- OS: Windows
- Python: 3.12
- CPU: AMD Ryzen 7 5700X
- RAM: 32GB
- GPU: NVIDIA GeForce RTX 4070 12GB
- Environment: Anaconda

※ 本実装ではOpenAI APIを利用しているため、GPUは必須ではありません。
