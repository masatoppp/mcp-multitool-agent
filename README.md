# MCP Multi-Tool Agent

MCP（Model Context Protocol）を利用し、複数のPython関数をToolとして公開し、LLMがユーザーの質問内容に応じて適切なToolと引数を選択する仕組みを実装しました。

MCP ClientがServerからTool定義を取得し、OpenAIのFunction Calling形式へ変換してLLMへ渡します。LLMが選択したToolはMCP Client経由でServer側へ実行要求され、Toolの実行結果を用いて最終回答を生成します。

## 概要

MCP Server側に複数のToolを登録し、MCP Clientから `list_tools()` を使用して利用可能なTool定義を取得します。

取得したTool情報をOpenAIのFunction Calling形式へ変換してLLMへ渡すことで、Client側にToolごとの `if / elif` を固定的に記述せず、LLMが質問内容に応じて適切なToolと引数を選択できる構成としています。

LLMが選択したTool名と引数をMCP Clientが受け取り、`call_tool()` を使用してMCP Serverへ実行を要求します。

実際のファイル読込や検索などの処理はServer側に登録したTool関数が行い、その実行結果をClient経由で再度LLMへ渡します。

LLMは元のユーザー質問とToolの実行結果をもとに、ユーザー向けの最終回答を生成します。

```text
ユーザーの質問
↓
MCP ClientがServerからTool定義を取得
    list_tools()
↓
MCP Tool定義をOpenAI Function Calling形式へ変換
↓
質問 + Tool定義をLLMへ送信
↓
LLMが使用するToolと引数を選択
↓
MCP Clientがcall_tool()でServerへ実行要求
↓
MCP Server側のTool関数が実処理
↓
Tool実行結果をMCP Clientへ返す
↓
Tool結果をLLMへ渡す
↓
LLMが最終回答を生成
↓
ユーザーへ回答
```

## 主なTool

本実装では、以下の5つのToolをMCP Serverへ登録しています。

```text
read_text_file
→ 指定したテキストファイルを読み込む

list_files
→ 指定したフォルダ直下のファイル一覧を取得する

get_file_info
→ ファイル名・拡張子・サイズ・存在有無を取得する

search_folder_text
→ フォルダ直下のテキストファイルから
   キーワードを含む行を検索する

count_keyword
→ フォルダ直下の各テキストファイルについて
   キーワードの出現回数を取得する
```

各ToolはPython関数として実装し、`@mcp.tool()` デコレータによってMCP ToolとしてServerへ登録しています。

```python
@mcp.tool()
def read_text_file(path: str) -> str:
    """指定したテキストファイルの内容を読み込みます。"""
```

Tool名、docstringによるdescription、引数schemaなどの情報をMCP Clientが取得し、OpenAIのFunction Calling形式へ変換してLLMへ渡します。

LLMはこれらのTool定義とユーザーの質問内容をもとに、使用するToolと引数を判断します。

## MCP Server / Client / LLMの役割

本実装では、MCP Server・MCP Client・LLMの責務を分離しています。

```text
MCP Server
→ Toolを登録・公開する
→ Clientから要求されたToolを実際に実行する

MCP Client
→ ServerからTool定義を取得する
→ Tool定義をOpenAI形式へ変換してLLMへ渡す
→ LLMが選択したTool名と引数を受け取る
→ call_tool()でServerへTool実行を要求する
→ Toolの実行結果をLLMへ返す

LLM
→ ユーザーの質問とTool定義を確認する
→ 使用するToolと引数を選択する
→ Tool実行結果をもとに最終回答を生成する
```

Toolの選択はMCP ClientやMCP ServerではなくLLMが行い、ファイル操作などの実処理はServer側のTool関数が担当します。

## MCPを利用する利点

今回の実装では、Server側へ新しいToolを追加した場合でも、Client側にそのTool専用の分岐処理を追加する必要がありません。

```text
ServerへPython関数を追加
↓
@mcp.tool() でTool登録
↓
Clientが list_tools() でTool定義を取得
↓
OpenAI Function Calling形式へ変換
↓
LLMへTool情報を渡す
↓
LLMが必要に応じてToolと引数を選択
↓
Clientが call_tool() でServerへ実行要求
```

Client側ではTool名を固定的に列挙せず、Serverから取得したTool定義を動的に利用しています。

これにより、異なる処理をMCP Toolという共通形式で公開し、Client側から統一的に取得・実行要求できる構成としています。

## ファイル構成

```text
mcp-multitool-agent/
├─ 04_MCPを利用した複数Tool連携.ipynb
├─ server.py
├─ client.py
├─ requirements.txt
└─ data/
    ├─ AI利用ルール.txt
    ├─ PC申請.txt
    ├─ セキュリティ.txt
    ├─ 有給休暇.txt
    └─ 障害対応.txt
```

- `server.py` : MCP Serverおよび5つのToolを定義
- `client.py` : MCP Client、OpenAI API連携、Tool選択結果の取得、Tool実行要求、最終回答生成
- `requirements.txt` : 実行に必要なPythonパッケージ
- `data/` : 動作確認用のダミーテキストデータ
- `04_MCPを利用した複数Tool連携.ipynb` : MCPの構成と処理フローを段階的に解説

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

`client.py` では `server.py` で生成したMCP Serverインスタンスを読み込み、MCP ClientからTool定義取得およびTool実行要求を行います。

```python
from server import mcp
```

MCP ClientはServerから取得したTool定義をOpenAIのFunction Calling形式へ変換し、ユーザーの質問とともにLLMへ渡します。

LLMが返したTool名と引数をClientが受け取り、MCP Server側のToolを実行します。

Notebookで段階的に確認した処理を、最終的に `client.py` と `server.py` に分離しています。

### 実行

必要なライブラリをインストールします。

```bash
pip install -r requirements.txt
```

`OPENAI_API_KEY` を環境変数へ設定したうえで、以下を実行します。

```bash
python client.py
```

## 処理フロー

### 1. Tool定義の取得

MCP Clientから `list_tools()` を実行し、Server側に登録されているTool定義を取得します。

```python
tools_response = await mcp_client.list_tools()
```

この段階ではToolの実行は行わず、利用可能なToolの定義情報を取得します。

### 2. OpenAI Function Calling形式への変換

MCPから取得したTool定義と、OpenAI Function Callingが利用するTool定義は形式が異なります。

そのため、以下の情報をOpenAIが利用できる形式へ変換します。

```text
MCP Tool
name
description
input_schema

↓

OpenAI Function Calling
name
description
parameters
```

### 3. LLMによるTool選択

ユーザーの質問と利用可能なTool定義をLLMへ渡します。

LLMは質問内容とTool定義を確認し、Toolが必要な場合は使用するTool名と引数を `tool_calls` として返します。

```text
ユーザー質問
+
利用可能なTool定義
↓
LLM
↓
Tool名 + 引数
```

### 4. Tool名と引数の取得

LLMから返された `tool_calls` から、使用するTool名と引数を取得します。

```python
tool_name = tool_call.function.name
tool_args = json.loads(tool_call.function.arguments)
```

`function.arguments` はJSON文字列として返されるため、`json.loads()` を使用してPythonの辞書へ変換します。

### 5. Toolの実行

MCP Clientから `call_tool()` を使用してServer側へTool実行を要求します。

```python
tool_result = await mcp_client.call_tool(
    tool_name,
    tool_args
)
```

`call_tool()` を呼び出すのはMCP Clientですが、ファイル読込や検索などの具体的な処理はServer側に登録されたTool関数が実行します。

### 6. Tool実行結果の取得

MCP Serverから返されたTool実行結果から、テキスト部分を取得します。

```python
tool_output = tool_result.content[0].text
```

### 7. 最終回答の生成

元のユーザー質問、LLMが生成したTool Call、Tool実行結果を再度LLMへ渡します。

```text
元のユーザー質問
+
LLMによるTool Call
+
Tool実行結果
↓
LLM
↓
ユーザー向け最終回答
```

Toolの生の実行結果をそのまま返すのではなく、元の質問の意図に沿った自然言語の回答へ整形します。

## 実装上のポイント

本実装では、以下の点を意識しています。

- Toolの実処理をMCP Server側へ集約
- MCP ClientはTool定義取得と実行要求を担当
- Tool選択はLLMが担当
- Client側にToolごとの固定的な `if / elif` を持たせない
- MCP Tool定義をOpenAI Function Calling形式へ変換
- Tool実行結果と最終回答生成を分離

これにより、Toolを追加する際もClient側のTool選択ロジックを個別に追加せず、Server側のTool定義を拡張できる構成としています。

## 実装範囲と制約

今回はMCPの基本的なTool連携を確認することを目的として、シンプルな構成としています。

現在の実装には以下の制約があります。

- 1回の応答では `tool_calls[0]` の先頭1件を処理
- Tool結果は `content[0].text` の先頭テキスト要素を利用
- 詳細な例外処理は未実装
- Toolごとのアクセス制御は未実装
- MCP ClientとServerは同一プロセス内で接続

## 今後の発展案

今後は以下のような拡張が考えられます。

- 複数Tool Callへの対応
- 複数Toolの連続実行
- Tool実行失敗時のエラーハンドリング
- Toolごとのアクセス制御
- stdio / Streamable HTTPを利用した別プロセス接続
- UIとの連携
- Tool実行履歴のログ・可観測性の追加

## Notebook

MCP Server / Client / LLMの役割、Tool定義取得、Function Calling形式への変換、Tool選択、Tool実行、最終回答生成までの処理は、以下のNotebookで段階的に確認できます。

**`04_MCPを利用した複数Tool連携.ipynb`**

Notebookでは、特に以下の点を確認しています。

- `@mcp.tool()` によるTool登録
- `list_tools()` によるTool定義取得
- MCP Tool定義からOpenAI Function Calling形式への変換
- LLMによるTool選択
- `tool_calls` からTool名・引数を取得
- `call_tool()` によるServer側Toolの実行
- Tool実行結果を利用した最終回答生成

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
