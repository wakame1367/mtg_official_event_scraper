#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import scrapy
import pandas as pd
import re
from datetime import datetime
from icalendar import Calendar, Event
import pytz
import os
import argparse
from urllib.parse import urlencode
import logging # logging モジュールをインポート

# logging の基本的な設定 (main 関数内で呼び出す)
def setup_logging(log_level=logging.INFO):
    logging.basicConfig(level=log_level,
                        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

# Spider クラスの logger を取得
logger = logging.getLogger(__name__) # Spider 内で使う logger

class MtgEventSpider(scrapy.Spider):
    name = 'mtg_event_spider'
    allowed_domains = ['mtg-jp.com']
    base_url = "https://mtg-jp.com/events/search/format/"
    # output_dir は __init__ で受け取るように変更

    def __init__(self, start_date=None, end_date='', prefecture='13', keyword='', output_dir='mtg_events_scrapy', *args, **kwargs):
        super(MtgEventSpider, self).__init__(*args, **kwargs)
        self.start_date = start_date if start_date else datetime.now().strftime('%Y/%m/%d')
        self.end_date = end_date
        self.prefecture = prefecture
        self.keyword = keyword
        self.output_dir = output_dir
        self.page = 1
        self.events = []

        # 開始URLを生成
        params = {
            'fmt': '',
            'exclude': '',
            'pref': self.prefecture,
            'freeword': self.keyword,
            'startDate': self.start_date,
            'endDate': self.end_date
        }
        params = {k: v for k, v in params.items() if v}
        query_string = urlencode(params)
        self.start_urls = [f"{self.base_url}?{query_string}#searchBlock"]

        logger.info(f"Spider initialized. Output directory: {self.output_dir}")
        logger.info(f"Scraping started with URL: {self.start_urls[0]}")
        os.makedirs(self.output_dir, exist_ok=True)


    def parse(self, response):
        logger.info(f"Parsing page {self.page} from URL: {response.url}")
        event_rows = response.css('table tr')

        events_found_on_page = False
        for row in event_rows:
            date_cell_text = row.css('.td-date ::text').get()
            if not date_cell_text:
                continue

            events_found_on_page = True
            date_match = re.search(r'(\d{4}\.\d{1,2}\.\d{1,2})', date_cell_text)
            time_match = re.search(r'(\d{1,2}:\d{2})～', date_cell_text)

            date_str = date_match.group(1).replace('.', '/') if date_match else ""
            time_str = time_match.group(1) if time_match else "00:00"

            location = row.css('.td-prefecture ::text').get(default="").strip()
            title = row.css('.td-info dt:first-child ::text').get(default="").strip()
            shop_name = row.css('.td-info dt a ::text').get() # まずリンク付きを試す
            if shop_name:
                shop_name = shop_name.strip()
            else: # リンクがない場合 (より具体的にセレクタを指定)
                # 例: <dt>店舗名</dt> のような場合
                # 次のdt要素を取得するなど、実際のHTML構造に合わせて調整
                shop_dt_elements = row.css('.td-info dt')
                if len(shop_dt_elements) > 1:
                    shop_name = shop_dt_elements[1].css('::text').get(default="").strip()
                else:
                     shop_name = "" # 見つからない場合は空文字

            format_text = row.css('.td-format ::text').get(default="").strip()

            if date_str:
                event_data = {
                    'date': date_str,
                    'time': time_str,
                    'location': location,
                    'title': title,
                    'shop': shop_name,
                    'format': format_text
                }
                self.events.append(event_data)
                logger.debug(f"Event found: {event_data}") # DEBUGレベルで詳細情報を記録

        # 次のページへのリンクを探す (前回と同様のロジック)
        next_page_link = response.xpath("//ul[@class='pager-list']//a[span[text()='>']]/@href").get()
        # 次のページのリンクが見つかった場合、リクエストを生成
        if next_page_link:
            # response.follow は相対URL (?p=20&...) を絶対URLに自動で解決
            logger.info(f"Found next page link: {next_page_link}. Following to page {self.page + 1}")
            self.page += 1 # ページ番号をインクリメント (ログ表示用など)
            yield response.follow(next_page_link, callback=self.parse)
        else:
            # 「>」リンクが見つからない場合は、最後のページである可能性が高い
            logger.info("No '>' link found in pagination. Assuming it's the last page.")


    def closed(self, reason):
        """
        スパイダーが終了したときに呼び出されるメソッド
        """
        logger.info(f"Spider closed: {reason}")
        if not self.events:
            logger.warning("No events were scraped.") # 警告レベルに変更
            return

        logger.info(f"{len(self.events)} events found.")

        # iCalendarファイルの作成
        try:
            ics_file = os.path.join(self.output_dir, "mtg_events.ics")
            self.create_ics_file(self.events, ics_file)
            logger.info(f"iCalendar file created successfully: {ics_file}")
        except Exception as e:
            logger.error(f"Failed to create iCalendar file: {e}", exc_info=True) # エラー詳細を記録

        # CSVファイルの作成
        try:
            csv_file = os.path.join(self.output_dir, "mtg_events.csv")
            self.create_csv_file(self.events, csv_file)
            logger.info(f"CSV file created successfully: {csv_file}")
        except Exception as e:
            logger.error(f"Failed to create CSV file: {e}", exc_info=True) # エラー詳細を記録


    def create_ics_file(self, events, output_file):
        """
        イベント情報からiCalendarファイルを作成する関数
        """
        cal = Calendar()
        cal.add('prodid', '-//MTG-JP Events Scrapy//manus.ai//')
        cal.add('version', '2.0')
        jst = pytz.timezone('Asia/Tokyo')

        for event_data in events:
            event = Event()
            event.add('summary', f"{event_data['title']} @ {event_data['shop']}")
            datetime_str = f"{event_data['date']} {event_data['time']}"
            try:
                event_datetime = datetime.strptime(datetime_str, '%Y/%m/%d %H:%M')
                event_datetime = jst.localize(event_datetime)
                event.add('dtstart', event_datetime)
                end_datetime = event_datetime + pd.Timedelta(hours=3)
                event.add('dtend', end_datetime)
            except ValueError as e:
                # print を logger.warning に変更
                logger.warning(f"ICS Warning: Could not parse datetime {datetime_str} for event '{event_data['title']}'. Skipping event. Error: {e}")
                continue

            location_text = f"{event_data['shop']} ({event_data['location']})"
            event.add('location', location_text)
            description = f"フォーマット: {event_data['format']}\n"
            description += f"開催店舗: {event_data['shop']}\n"
            description += f"開催地: {event_data['location']}\n"
            description += f"MTG-JP イベント情報より ({self.start_urls[0]})"
            event.add('description', description)
            cal.add_component(event)

        with open(output_file, 'wb') as f:
            f.write(cal.to_ical())
        return output_file

    def create_csv_file(self, events, output_file):
        """
        イベント情報からCSVファイルを作成する関数
        """
        df = pd.DataFrame(events)
        if not df.empty:
            df = df[['date', 'time', 'location', 'title', 'shop', 'format']]
        else:
             logger.warning("DataFrame is empty. Cannot create CSV content properly.")
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        return output_file

# --- main 関数と Scrapy 実行 ---
def main():
    """
    コマンドライン引数を処理し、Scrapy スパイダーを実行するメイン関数
    """
    # ロギング設定を呼び出し
    setup_logging()

    parser = argparse.ArgumentParser(description='MTG-JPイベント情報をスクレイピングし、ICS/CSVファイルを出力します。')
    parser.add_argument('--start-date', type=str, help='検索開始日 (YYYY/MM/DD形式)。デフォルトは今日。')
    parser.add_argument('--end-date', type=str, default='', help='検索終了日 (YYYY/MM/DD形式)。')
    parser.add_argument('--prefecture', type=str, default='13', help='都道府県コード (例: 13 は東京都)。デフォルトは13。')
    parser.add_argument('--keyword', type=str, default='', help='検索キーワード (イベント名、フォーマットなど)。')
    parser.add_argument('--output-dir', type=str, default='mtg_events_scrapy', help='出力ディレクトリ名。デフォルトは mtg_events_scrapy。')
    parser.add_argument('--log-level', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='ログレベルを設定します (デフォルト: INFO)')

    args = parser.parse_args()

    # コマンドライン引数で指定されたログレベルで再設定
    log_level_numeric = getattr(logging, args.log_level.upper(), logging.INFO)
    setup_logging(log_level=log_level_numeric)

    logger.info("Starting Scrapy process...")
    logger.debug(f"Arguments: {args}") # DEBUGレベルで引数を記録

    # Scrapyを実行するための準備
    from scrapy.crawler import CrawlerProcess
    from scrapy.settings import Settings

    # Scrapyの設定
    settings = Settings()
    # Scrapy自身のログ設定も考慮 - Pythonのlogging設定が優先されることが多いが、
    # 必要ならここでScrapy固有のログ設定も追加可能
    settings['LOG_LEVEL'] = args.log_level.upper() # Scrapyのログレベルも引数に合わせる
    settings['LOG_FORMAT'] = '%(asctime)s [%(name)s] %(levelname)s: %(message)s' # Scrapyログのフォーマット例
    settings['LOG_DATEFORMAT'] = '%Y-%m-%d %H:%M:%S'
    # 標準のloggingを使う場合、ScrapyのLOG_ENABLED=Falseも考慮するが、通常は不要
    # settings['LOG_ENABLED'] = True # デフォルトはTrue

    settings['USER_AGENT'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36' # UserAgent例
    settings['ROBOTSTXT_OBEY'] = False # robots.txtに従うか (注意して設定)
    settings['DOWNLOAD_DELAY'] = 1    # ダウンロード遅延 (秒)
    settings['CONCURRENT_REQUESTS_PER_DOMAIN'] = 8

    process = CrawlerProcess(settings)

    process.crawl(MtgEventSpider,
                  start_date=args.start_date,
                  end_date=args.end_date,
                  prefecture=args.prefecture,
                  keyword=args.keyword,
                  output_dir=args.output_dir)

    try:
        process.start() # the script will block here until the crawling is finished
        logger.info("Scrapy process finished successfully.")
    except Exception as e:
        logger.critical(f"An error occurred during the Scrapy process: {e}", exc_info=True)

if __name__ == '__main__':
    main()