# mtg_official_event_scraper

マジック・ザ・ギャザリング日本公式サイトからイベント情報をスクレイピングして、iCalendarファイル（.ics）とCSVファイルを自動生成するツールです。

## 概要

このツールは、[マジック：ザ・ギャザリング日本公式サイト](https://mtg-jp.com/events/)からイベント情報を収集し、カレンダーアプリで購読できる形式（.ics）と表計算ソフトで扱いやすい形式（.csv）に変換します。GitHub Actionsを使って定期的に実行し、GitHub Pagesで公開することもできます。

## 必要条件

- Python 3.13以上
- uvパッケージマネージャー（推奨）

## インストール方法

### 1. リポジトリのクローン

```bash
git clone https://github.com/yourusername/mtg_official_event_scraper.git
cd mtg_official_event_scraper
```

### 2. 依存パッケージのインストール


```bash
uv sync --all-extras --dev
```

### 3. スクリプト実行

```bash
uv run mtg-official-event-scraper --output-dir output
```

オプションを指定して実行する場合：
```bash
mtg-official-event-scraper \
    --output-dir output \
    --start-date 2025-04-01 \
    --end-date 2025-06-01 \
    --prefecture 13 \
    --keyword PWS \
    --log-level INFO
```

## 主なオプション

- `--output-dir`: 出力ファイルを保存するディレクトリ（デフォルト: `mtg_events_scrapy`）
- `--start-date`: 検索開始日（YYYY/MM/DD形式、デフォルト: 今日）
- `--end-date`: 検索終了日（YYYY/MM/DD形式、指定しない場合は制限なし）
- `--prefecture`: 都道府県コード（例: 13は東京都、デフォルト: 13）
- `--keyword`: 検索キーワード（例: フォーマット名やイベント名）
- `--log-level`: ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL、デフォルト: INFO）

## GitHub Actionsによる自動デプロイ

このリポジトリには、GitHub Actionsのワークフローが設定されています。`.github/workflows/update_calendar.yml`ファイルにより、以下の機能が実現されています：

1. **定期実行**: 毎日日本時間午前3時（UTC 18:00）に自動実行
2. **手動実行**: GitHub上で手動トリガーによる実行も可能
3. **プッシュ時実行**: mainブランチへのプッシュ時にも自動実行
4. **GitHub Pagesへの自動デプロイ**: 生成したiCalendarファイルとCSVファイルを公開

### GitHub Actionsの設定変更方法

ワークフローの設定を変更するには、`.github/workflows/update_calendar.yml`ファイルを編集します：

```bash
# スクレイピングのパラメータを変更する例
- name: Run Scrapy scraper
  run: |
    uv run mtg-official-event-scraper \
      --output-dir output \
      --log-level INFO \
      --start-date 2025-04-01 \
      --end-date 2025-06-01 \
      --prefecture 13 \
      --keyword PWS
```

## GitHub Pagesの利用方法

GitHub Actionsによって自動デプロイされたページの使い方は以下の通りです：

### 1. カレンダーに登録する

生成されたiCalendarファイルをカレンダーアプリに登録することで、MTGイベント情報を自動的に取得できます。

#### Googleカレンダーの場合:
1. Googleカレンダーを開く
2. 左側の「他のカレンダー」の横にある「+」をクリック
3. 「URLで追加」を選択
4. 以下のURLを入力:
   ```
   https://yourusername.github.io/mtg_official_event_scraper/mtg_events.ics
   ```
5. 「カレンダーを追加」をクリック

#### iPhoneカレンダーの場合:
1. 「設定」アプリを開く
2. 「カレンダー」→「アカウント」→「アカウントを追加」→「その他」を選択
3. 「照会するカレンダーを追加」をタップ
4. 同じURLを入力して登録

### 2. CSVファイルのダウンロード

表計算ソフトでイベント情報を分析したい場合は、以下のURLからCSVファイルを直接ダウンロードできます：

```
https://yourusername.github.io/mtg_official_event_scraper/mtg_events.csv
```

### 注意事項

- カレンダーの更新頻度は1日1回です（日本時間午前3時頃）
- GitHub Pagesの反映には数分かかることがあります
- リポジトリ名やユーザー名を変更した場合は、URLも変更されます

## ライセンス

MIT License