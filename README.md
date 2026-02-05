# 財經政治新聞搜集器

這是一個透過 RSS/Atom Feed 抓取財經與政治新聞的簡易工具，輸出 JSON 方便後續分析或整合。

## 特色
- 預設內建多個財經、政治新聞來源（含 The Economist、Wall Street Journal、Financial Times）。
- 支援輸出 JSON 檔案。
- 可設定抓取筆數上限與請求間隔。
- 會依標題關鍵字將新聞分類為地區（美國/歐洲/日本/台灣/中國/其他地區）與主題（財政政策/經濟政策/政治動態/產業消息）。

## 使用方式
```bash
python3 news_collector.py --output news.json
```

### 常用參數
- `--limit`：限制輸出筆數。
- `--output`：指定輸出檔案路徑。
- `--sleep`：每個來源之間的等待秒數。

範例：
```bash
python3 news_collector.py --limit 30 --output data/news.json --sleep 1
```

## 輸出格式
```json
{
  "generated_at": "2024-01-01T00:00:00Z",
  "count": 10,
  "items": [
    {
      "source": "Reuters Business",
      "category": "finance",
      "region": "美國",
      "topic": "經濟政策",
      "title": "...",
      "link": "...",
      "published": "..."
    }
  ]
}
```

## 注意事項
- RSS 來源可能因地區或網路限制而無法存取。
- 若需擴充來源，可在 `news_collector.py` 的 `DEFAULT_SOURCES` 中新增。
