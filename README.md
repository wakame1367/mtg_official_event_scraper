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

uvを使う場合:
```bash
uv sync --all-extras --dev
```

pipを使う場合:
```bash
pip install -e
```