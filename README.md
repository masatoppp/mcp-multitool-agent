# MCP Multi-Tool Agent

MCP（Model Context Protocol）を利用し、複数のPython関数をToolとして公開し、LLMがユーザーの質問内容に応じて適切なToolを選択・実行する仕組みを実装しました。

## 概要

MCP Server側に複数のToolを登録し、MCP Clientから `list_tools()` を使用して利用可能なTool定義を取得します。

取得したTool情報をOpenAIのFunction Calling形式へ変換してLLMへ渡すことで、Client側にToolごとの `if / elif` を固定的に記述せず、LLMが質問内容に応じて適切なToolと引数を選択できる構成としています。

LLMが選択したToolはMCP Clientから `call_tool()` を通してMCP Serverへ実行要求され、Server側のTool関数が実際の処理を行います。

Toolの実行結果は再度LLMへ渡し、ユーザーの質問に沿った自然言語の最終回答を生成します。

```text
ユーザーの質問
↓
MCP ClientがServerからTool定義を取得
↓
質問 + Tool情報をLLMへ送信
↓
LLMが使用するToolと引数を選択
↓
MCP Clientがcall_tool()でServerへ実行要求
↓
MCP Server側のToolを実行
↓
Tool実行結果をMCP Clientへ返す
↓
Tool結果をLLMへ渡す
↓
最終回答を生成
```

## 主なTool

```text
read_text_file
→ 指定したテキストファイルを読み込む

list_files
→ 指定したフォルダ直下のファイル一覧を取得する

get_file_info
→ ファイル名・拡張子・サイズ・存在有無を取得する

search_folder_text
→ フォルダ内の複数テキストファイルからキーワードを含む行を検索する

count_keyword
→ ファイルごとにキーワードの出現回数を取得する
```

各ToolはPython関数として実装し、`@mcp.tool()` デコレータによってMCP ToolとしてServerへ登録しています。

Tool名、docstringによるdescription、引数schemaなどの情報をMCP Clientが取得し、OpenAIのFunction Calling形式へ変換してLLMへ渡します。

LLMはこれらのTool定義とユーザーの質問をもとに、使用するToolと引数を判断します。

## MCP Server / Client / LLMの役割

本実装では、それぞれ次の役割を持たせています。

```text
MCP Server
→ Toolを登録・公開する
→ Clientから要求されたToolを実際に実行する

MCP Client
→ ServerからTool定義を取得する
→ Tool定義をLLMへ渡す
→ LLMが選択したToolをServerへ実行要求する
→ Toolの実行結果をLLMへ返す

LLM
→ ユーザーの質問とTool定義を確認する
→ 使用するToolと引数を選択する
→ Tool実行結果をもとに最終回答を生成する
```

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
LLMが必要に応じてToolを選択
↓
Clientが call_tool() でServerへ実行要求
```

異なる処理をMCP Toolという共通形式で公開し、Client側から統一的に取得・実行できる構成を確認しました。

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

- `server.py` : MCP ServerおよびTool定義
- `client.py` : MCP Client、OpenAI API連携、Tool選択・実行、最終回答生成
- `requirements.txt` : 実行に必要なPythonパッケージ
- `data/` : 動作確認用のダミーテキストデータ
- Notebook : MCPの構成、Server / Clientの役割、Tool選択から実行までの処理フローを解説

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

MCP Server側にファイル操作用のToolを登録し、Client側からServerが公開しているTool定義を取得します。

Clientは取得したTool定義をOpenAIのFunction Calling形式へ変換してLLMへ渡し、LLMが選択したToolをMCP経由でServer側に実行要求します。

最終的にNotebookで確認した処理を `client.py` と `server.py` に分離し、Pythonスクリプトとしても実行できる構成としています。

```text
python client.py
```

## 処理フロー

### 1. Tool定義の取得

MCP Clientから `list_tools()` を実行し、Server側に登録されているTool定義を取得します。

### 2. OpenAI形式への変換

取得したTool名・description・引数schemaをOpenAIのFunction Calling形式へ変換します。

### 3. LLMによるTool選択

ユーザーの質問と利用可能なTool情報をLLMへ渡し、使用するToolと引数を判断させます。

### 4. Toolの実行

LLMが返したTool名と引数を取得し、MCP Clientから `call_tool()` を使用してServer側のToolを実行します。

### 5. 最終回答生成

Toolの実行結果をLLMへ返し、元のユーザー質問に沿った自然言語の回答を生成します。

## 実装範囲

今回はMCPの基本的なTool連携を確認することを目的として、1回の質問につき先頭のTool呼び出し1件を処理するシンプルな構成としています。

また、Toolの実行結果についても先頭のテキスト要素を利用しています。

今後は、以下のような拡張が可能です。

- 複数Toolの連続実行
- 複数Tool Callへの対応
- Tool実行時のエラー処理
- Toolごとの権限制御
- リモートMCP Serverとの接続
- UIとの連携

## Notebook

実装内容、MCP Server / Client / LLMの役割、`list_tools()` と `call_tool()` の違い、Tool選択から実行結果を最終回答へ反映するまでの処理は、以下のNotebookで解説しています。

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
