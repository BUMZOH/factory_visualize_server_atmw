# JSON形式の機械設定ファイルの操作法

#JSON #Python #設定ファイル #設備監視 #PLCデバイス

## はじめに

この資料では、機械Noごとの設定をJSONファイルで管理し、Pythonから読み込んで利用する方法を解説します。

対象とするJSONファイルでは、機械Noごとに以下の情報を管理します。

- 説明文
- 有効 / 無効
- ステータスデバイス
- 実績生産数デバイス
- 目標生産数デバイス
- アラーム数デバイス

設備監視プログラムでは、機械ごとにPLCデバイス番号が異なることがあります。
そのため、これらをJSONファイルにまとめておくと、Pythonプログラム本体を変更せずに設定変更できるようになります。

---

## JSONファイル例

ファイル名を `machine_config.json` とします。

```json
{
    "machines": {
        "45": {
            "description": "drilling machine",
            "enable": true,
            "status_device": "DM400",
            "actual_count_device": "DM500",
            "target_count_device": "DM600",
            "alarm_count_device": "DM700"
        },
        "47": {
            "description": "hole-inspecting machine",
            "enable": true,
            "status_device": "DM401",
            "actual_count_device": "DM501",
            "target_count_device": "DM601",
            "alarm_count_device": "DM701"
        }
    }
}
```

---

## JSON構造の考え方

このJSONは、以下のような階層構造になっています。

```text
machine_config.json
└── machines
    ├── 45
    │   ├── description
    │   ├── enable
    │   ├── status_device
    │   ├── actual_count_device
    │   ├── target_count_device
    │   └── alarm_count_device
    │
    └── 47
        ├── description
        ├── enable
        ├── status_device
        ├── actual_count_device
        ├── target_count_device
        └── alarm_count_device
```

`machines` の中に、機械Noごとの設定を格納しています。

```json
"machines": {
    "45": {
        ...
    },
    "47": {
        ...
    }
}
```

ここで重要なのは、`"45"` や `"47"` が機械Noを表していることです。

JSONではキーは文字列として扱われます。
そのため、Pythonからアクセスするときも、基本的には以下のように文字列で指定します。

```python
config["machines"]["45"]
```

---

## サンプルプログラム全体

ファイル名を `main.py` とします。

```python
import json
from pathlib import Path


CONFIG_FILE = Path("machine_config.json")


def load_config():
    """JSON設定ファイルを読み込む"""
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def show_machine_45(config):
    """機械No.45の設定を表示する"""
    machine = config["machines"]["45"]

    print("=== 機械No.45 ===")
    print("説明:", machine["description"])
    print("有効:", machine["enable"])
    print("ステータスデバイス:", machine["status_device"])
    print("実績生産数デバイス:", machine["actual_count_device"])
    print("目標生産数デバイス:", machine["target_count_device"])
    print("アラーム数デバイス:", machine["alarm_count_device"])


def show_all_machines(config):
    """全機械の設定を順番に表示する"""
    print("=== 全機械一覧 ===")

    for machine_no, machine in config["machines"].items():
        print("--------------------")
        print("機械No:", machine_no)
        print("説明:", machine["description"])
        print("有効:", machine["enable"])
        print("ステータスデバイス:", machine["status_device"])
        print("実績生産数デバイス:", machine["actual_count_device"])
        print("目標生産数デバイス:", machine["target_count_device"])
        print("アラーム数デバイス:", machine["alarm_count_device"])


def show_enabled_machines(config):
    """有効な機械だけを表示する"""
    print("=== 有効な機械だけ表示 ===")

    for machine_no, machine in config["machines"].items():
        if not machine["enable"]:
            continue

        print("--------------------")
        print("機械No:", machine_no)
        print("説明:", machine["description"])
        print("ステータスデバイス:", machine["status_device"])


def main():
    config = load_config()

    show_machine_45(config)
    print()

    show_all_machines(config)
    print()

    show_enabled_machines(config)


if __name__ == "__main__":
    main()
```

---

## 実行方法

同じフォルダに以下の2ファイルを置きます。

```text
project_folder/
├── main.py
└── machine_config.json
```

コマンドプロンプト、PowerShell、VS Codeのターミナルなどで以下を実行します。

```bash
python main.py
```

---

## JSONファイルの読み込み

```python
import json
from pathlib import Path

CONFIG_FILE = Path("machine_config.json")


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
```

### 解説

`json` モジュールは、Python標準ライブラリです。
追加インストールは不要です。

```python
json.load(f)
```

とすることで、JSONファイルの内容をPythonの辞書として読み込めます。

JSONの

```json
{
    "machines": {
        "45": {
            "enable": true
        }
    }
}
```

は、Pythonでは次のような辞書として扱えます。

```python
config = {
    "machines": {
        "45": {
            "enable": True
        }
    }
}
```

JSONの `true` は、Pythonでは `True` になります。

---

## 機械No.45の設定へアクセスする

```python
machine = config["machines"]["45"]
```

この1行で、機械No.45の設定を取得できます。

取得した `machine` の中身は、以下のような辞書です。

```python
{
    "description": "drilling machine",
    "enable": True,
    "status_device": "DM400",
    "actual_count_device": "DM500",
    "target_count_device": "DM600",
    "alarm_count_device": "DM700"
}
```

---

## 各値へのアクセス

### descriptionを取得

```python
description = config["machines"]["45"]["description"]
print(description)
```

出力例：

```text
drilling machine
```

---

### enableを取得

```python
enable = config["machines"]["45"]["enable"]
print(enable)
```

出力例：

```text
True
```

`enable` は `true` / `false` の値なので、Pythonでは `True` / `False` として扱えます。

例えば、有効な機械だけ処理したい場合は以下のように書けます。

```python
if config["machines"]["45"]["enable"]:
    print("機械No.45は有効です")
```

---

### ステータスデバイスを取得

```python
status_device = config["machines"]["45"]["status_device"]
print(status_device)
```

出力例：

```text
DM400
```

---

### 実績生産数デバイスを取得

```python
actual_count_device = config["machines"]["45"]["actual_count_device"]
print(actual_count_device)
```

出力例：

```text
DM500
```

---

### 目標生産数デバイスを取得

```python
target_count_device = config["machines"]["45"]["target_count_device"]
print(target_count_device)
```

出力例：

```text
DM600
```

---

### アラーム数デバイスを取得

```python
alarm_count_device = config["machines"]["45"]["alarm_count_device"]
print(alarm_count_device)
```

出力例：

```text
DM700
```

---

## 変数に入れてからアクセスする書き方

毎回以下のように書くと、少し長くなります。

```python
config["machines"]["45"]["status_device"]
config["machines"]["45"]["actual_count_device"]
config["machines"]["45"]["target_count_device"]
```

そのため、先に機械No.45の設定だけを変数に入れると読みやすくなります。

```python
machine_45 = config["machines"]["45"]

print(machine_45["description"])
print(machine_45["status_device"])
print(machine_45["actual_count_device"])
print(machine_45["target_count_device"])
print(machine_45["alarm_count_device"])
```

この書き方の方が、実務では読みやすいです。

---

## 全機械をループ処理する

全機械を順番に処理する場合は、`items()` を使います。

```python
for machine_no, machine in config["machines"].items():
    print(machine_no)
    print(machine["description"])
```

### 解説

`config["machines"]` は、以下のような辞書です。

```python
{
    "45": {...},
    "47": {...}
}
```

この辞書に対して `.items()` を使うと、キーと値を同時に取り出せます。

```python
for machine_no, machine in config["machines"].items():
```

このとき、1回目のループでは以下のようになります。

```python
machine_no = "45"
machine = {
    "description": "drilling machine",
    "enable": True,
    "status_device": "DM400",
    "actual_count_device": "DM500",
    "target_count_device": "DM600",
    "alarm_count_device": "DM700"
}
```

2回目のループでは以下のようになります。

```python
machine_no = "47"
machine = {
    "description": "hole-inspecting machine",
    "enable": True,
    "status_device": "DM401",
    "actual_count_device": "DM501",
    "target_count_device": "DM601",
    "alarm_count_device": "DM701"
}
```

---

## 有効な機械だけ処理する

`enable` が `true` の機械だけ処理する場合は、以下のようにします。

```python
for machine_no, machine in config["machines"].items():
    if not machine["enable"]:
        continue

    print("機械No:", machine_no)
    print("説明:", machine["description"])
    print("ステータスデバイス:", machine["status_device"])
```

### 解説

```python
if not machine["enable"]:
    continue
```

これは、`enable` が `False` の場合は処理をスキップするという意味です。

例えばJSONが以下のようになっていた場合、

```json
{
    "machines": {
        "45": {
            "enable": true
        },
        "47": {
            "enable": false
        }
    }
}
```

機械No.47は処理されません。

実務では、設備を一時的に監視対象から外したい場合に便利です。

---

## 機械Noを数値として扱いたい場合

JSONのキーは文字列です。
そのため、以下のように取得されます。

```python
machine_no = "45"
```

もし数値として使いたい場合は、`int()` で変換します。

```python
machine_no_int = int(machine_no)
```

例：

```python
for machine_no, machine in config["machines"].items():
    machine_no_int = int(machine_no)
    print(machine_no_int)
```

ただし、通常の設定ファイル操作では、機械Noは文字列のままでも問題ありません。

```python
config["machines"]["45"]
```

のようにアクセスできるため、むしろ文字列のまま扱う方が自然な場面も多いです。

---

## PLC読取処理に使うイメージ

実際には、取得したデバイス名を使ってPLCから値を読むことになります。

ここではPLC通信部分を仮の関数にしています。

```python
def read_plc(device):
    """PLCから値を読む仮の関数"""
    print(f"PLC読取: {device}")
    return 0


for machine_no, machine in config["machines"].items():
    if not machine["enable"]:
        continue

    status = read_plc(machine["status_device"])
    actual_count = read_plc(machine["actual_count_device"])
    target_count = read_plc(machine["target_count_device"])
    alarm_count = read_plc(machine["alarm_count_device"])

    print("機械No:", machine_no)
    print("説明:", machine["description"])
    print("ステータス:", status)
    print("実績生産数:", actual_count)
    print("目標生産数:", target_count)
    print("アラーム数:", alarm_count)
```

このようにすると、PLCデバイス番号をPythonコードに直接書かず、JSON側で管理できます。

---

## 設定ファイル化するメリット

### Pythonコードを変更しなくてよい

例えば、機械No.45の実績生産数デバイスが `DM500` から `DM510` に変わった場合、JSONだけ変更すれば済みます。

```json
"actual_count_device": "DM510"
```

Pythonコード本体を変更しなくてよいため、保守が楽になります。

---

### 有効 / 無効を簡単に切り替えられる

一時的に機械No.47を監視対象から外したい場合は、以下のように変更するだけです。

```json
"47": {
    "description": "hole-inspecting machine",
    "enable": false,
    "status_device": "DM401",
    "actual_count_device": "DM501",
    "target_count_device": "DM601",
    "alarm_count_device": "DM701"
}
```

Python側で `enable` を見てスキップする処理を書いておけば、簡単に対象外にできます。

---

### 機械の説明を持たせられる

`description` を追加しておくと、機械Noだけでは分かりにくい場合に便利です。

```json
"description": "hole-inspecting machine"
```

画面表示、ログ出力、エラーメッセージなどに利用できます。

例：

```python
print(f"{machine_no}: {machine['description']}")
```

---

## 注意点

## 1. JSONではコメントを書けない

JSONファイルには、以下のようなコメントは書けません。

```json
// これはコメント
```

```json
{
    "machines": {
        "45": {
            // drilling machine
            "enable": true
        }
    }
}
```

これはエラーになります。

説明を書きたい場合は、今回のように `description` という項目を用意するのが安全です。

```json
"description": "drilling machine"
```

---

## 2. true / false は小文字で書く

JSONでは、真偽値は以下のように小文字で書きます。

```json
"enable": true
```

Pythonのように `True` と書くと、JSONとしては不正です。

間違い：

```json
"enable": True
```

正しい：

```json
"enable": true
```

---

## 3. キーはダブルクォーテーションで囲む

JSONでは、キーは必ずダブルクォーテーションで囲みます。

正しい：

```json
"status_device": "DM400"
```

間違い：

```json
status_device: "DM400"
```

---

## 4. 最後のカンマに注意する

JSONでは、最後の要素の後ろにカンマを書けません。

間違い：

```json
{
    "description": "drilling machine",
    "enable": true,
}
```

正しい：

```json
{
    "description": "drilling machine",
    "enable": true
}
```

---

## まとめ

今回のような機械設定は、JSONで管理するのに向いています。

おすすめ構造は以下です。

```json
{
    "machines": {
        "45": {
            "description": "drilling machine",
            "enable": true,
            "status_device": "DM400",
            "actual_count_device": "DM500",
            "target_count_device": "DM600",
            "alarm_count_device": "DM700"
        }
    }
}
```

ポイントは以下です。

- `machines` の中に機械Noごとの設定を入れる
- 機械NoはJSONキーとして管理する
- `description` を持たせると人間が見て分かりやすい
- `enable` で監視対象を切り替えられる
- PLCデバイス番号をPythonコードに直接書かず、JSON側で管理できる
- 全機械処理には `.items()` を使う
- 有効な機械だけ処理する場合は `enable` を確認する

この形にしておくと、将来機械台数が増えても、Pythonコードの変更を最小限にできます。

設備監視プログラムやPLCデータ収集プログラムの設定ファイルとして、かなり扱いやすい構成です。
