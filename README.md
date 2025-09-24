# Research Paper Scraper

A production-grade Python 3.11 scraper for extracting research papers from chemRxiv and OpenReview with comprehensive metadata extraction, OCR support, and discussion thread capture.

## Features

- **Multi-source scraping**: chemRxiv (public dashboard) and OpenReview (API)
- **Date range filtering**: Scrape papers from specific date windows
- **OCR support**: Automatic OCR for scanned PDFs using Tesseract
- **LaTeX math preservation**: Keeps mathematical notation intact
- **Discussion threads**: Full forum discussions from OpenReview
- **Rich metadata**: Title, abstract, authors, DOI, comments, subject, journal, etc.
- **Rate limiting**: Conservative backoff with exponential retry
- **Error handling**: Comprehensive error tracking and reporting
- **Multiple output formats**: JSONL records + CSV statistics

## Installation

### Prerequisites

- Python 3.11+
- Tesseract OCR (for scanned PDF processing)

### Install Tesseract

**Windows:**
```bash
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
# Or use chocolatey:
choco install tesseract
```

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

### Install Python Dependencies

```bash
# Install the package in development mode
pip install -e .

# Or install dependencies directly
pip install -r requirements.txt
```

### Install Playwright Browsers

```bash
playwright install chromium
```

## Configuration

The scraper uses YAML configuration files. See `configs/trial.yaml` for the default configuration:

```yaml
run_name: "trial-aug-2025"
output_dir: "data"
date_from: "2025-08-01"
date_to: "2025-08-31"

user_agent: "ResearchScrapeBot/0.1 (+contact: team@example.com)"
rate_limit:
  max_requests_per_minute: 12
  burst: 6
  backoff_initial_s: 1.0
  backoff_max_s: 30.0

concurrency:
  downloads: 4
  parsing: 4

sources: ["chemrxiv", "openreview"]

OCR:
  enabled: true
  language: "eng"

math:
  preserve_latex: true

chemrxiv:
  listing_url: "https://chemrxiv.org/engage/chemrxiv/public-dashboard"
  listing_wait_selector: "div[role='grid']"
  item_link_selector: "a[href*='/engage/chemrxiv/article/']"
  pdf_link_selector: "a[href$='.pdf']"

openreview:
  api_base: "https://api.openreview.net"
  search_path: "/notes/search"
  discussions_path: "/notes"
```

## Usage

### Basic Usage

```bash
# Run with trial configuration (25 records limit)
scrape trial --config configs/trial.yaml --limit 25

# Run full scrape
scrape run --config configs/trial.yaml

# Dry run mode (list what would be downloaded without fetching)
scrape trial --config configs/trial.yaml --limit 10 --dry-run
```

### Command Line Options

- `--config, -c`: Path to YAML configuration file
- `--limit`: Maximum number of records to process (trial mode only)
- `--dry-run`: List what would be downloaded without fetching files

### Using Make

```bash
# Setup environment
make setup

# Run tests
make test

# Run linting
make lint

# Run scraper in trial mode
make run

# Run scraper in dry-run mode
make run-dry

# Clean generated files
make clean
```

## Output Structure

```
data/
├── jsonl/
│   └── records.jsonl          # Main output: one JSON record per line
├── raw/
│   ├── chemrxiv/              # Downloaded PDFs from chemRxiv
│   └── openreview/            # Downloaded PDFs from OpenReview
├── clean/
│   └── *.txt                  # Extracted and cleaned text files
└── reports/
    ├── stats.csv              # Processing statistics
    ├── errors.csv             # Error log
    └── run_metrics.csv        # Performance metrics
```

## Data Model

Each record contains:

```json
{
  "source": "chemrxiv|openreview",
  "id": "unique_identifier",
  "title": "Paper Title",
  "abstract": "Abstract text",
  "authors": ["Author 1", "Author 2"],
  "date": "2025-08-15T10:30:00Z",
  "subject": "Chemistry",
  "journal": "Journal Name",
  "comments": "Additional comments",
  "doi": "10.1234/example",
  "revision": 1,
  "length_chars": 5000,
  "sections": 8,
  "source_url": "https://...",
  "file_type": "pdf",
  "raw_paths": {
    "pdf": "/path/to/file.pdf",
    "latex": null,
    "docx": null,
    "code": [],
    "data": [],
    "other": []
  },
  "clean_text_path": "/path/to/clean.txt",
  "discussions": [
    {
      "platform": "openreview",
      "thread_url": "https://...",
      "post_id": "post_123",
      "author": "Reviewer Name",
      "created": "2025-08-16T14:20:00Z",
      "body": "Comment text",
      "reply_to": null
    }
  ],
  "extra": {}
}
```

## Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_parsers.py

# Run with coverage
pytest --cov=src tests/
```

### Code Structure

```
src/scrape/
├── cli.py                 # Command-line interface
├── config.py             # Configuration management
├── models.py             # Data models (Record, etc.)
├── normalize.py          # Text normalization
├── dedupe.py             # Deduplication utilities
├── logging.py            # Logging setup
├── parsers/              # File parsers
│   ├── pdf_parser.py     # PDF text extraction + OCR
│   ├── latex_parser.py   # LaTeX processing
│   ├── docx_parser.py    # DOCX processing
│   └── guess_sections.py # Section detection
├── sources/              # Data sources
│   ├── base.py           # Base source class
│   ├── chemrxiv.py       # chemRxiv scraper
│   └── openreview.py     # OpenReview API client
├── exporters/            # Output formatters
│   ├── jsonl_writer.py   # JSONL output
│   └── stats.py          # Statistics generation
└── utils/                # Utilities
    ├── files.py          # File operations
    ├── http.py           # HTTP client
    ├── ocr.py            # OCR integration
    └── rate.py           # Rate limiting
```

## Rate Limiting

The scraper implements conservative rate limiting:

- **chemRxiv**: 12 requests/minute with 6-request bursts
- **OpenReview**: Respects API rate limits with exponential backoff
- **Automatic retry**: Failed requests are retried with increasing delays
- **Graceful degradation**: Continues processing even if some requests fail

## Error Handling

- **Comprehensive logging**: All operations are logged with appropriate levels
- **Error tracking**: Failed operations are recorded in `reports/errors.csv`
- **Graceful failures**: Individual record failures don't stop the entire process
- **Retry logic**: Network errors trigger automatic retries with backoff

## Performance

- **Concurrent processing**: Parallel downloads and parsing
- **Memory efficient**: Streams large files without loading entirely into memory
- **Progress tracking**: Real-time progress updates during processing
- **Resource management**: Proper cleanup of browser instances and file handles

## Reproducing the August Window Scrape

### Step-by-Step Instructions

1. **Setup Environment**:
   ```bash
   # Clone the repository
   git clone <repository-url>
   cd research-paper-scrape
   
   # Setup environment
   make setup
   ```

2. **Configure Date Range**:
   Edit `configs/trial.yaml` to set the desired date range:
   ```yaml
   date_from: "2024-08-01"
   date_to: "2024-08-31"
   ```

3. **Test with Dry Run**:
   ```bash
   # See what would be scraped without downloading
   make run-dry
   ```

4. **Run the Scraper**:
   ```bash
   # Run with limited records first
   make run
   
   # Or run full scrape
   make run-full
   ```

### Verifying Outputs

#### 1. Check JSONL Records
```bash
# View the first few records
head -n 5 data/jsonl/records.jsonl | jq '.'

# Count total records
wc -l data/jsonl/records.jsonl

# Check record structure
jq 'keys' data/jsonl/records.jsonl | head -n 1
```

#### 2. Verify Statistics
```bash
# View processing statistics
cat data/reports/stats.csv

# Check error log
cat data/reports/errors.csv

# View run metrics
cat data/reports/run_metrics.csv
```

#### 3. Validate Data Quality
```bash
# Check for records with PDFs
jq 'select(.raw_paths.pdf != null)' data/jsonl/records.jsonl | wc -l

# Check for records with discussions
jq 'select(.discussions != null and (.discussions | length) > 0)' data/jsonl/records.jsonl | wc -l

# Check average text length
jq -r '.length_chars' data/jsonl/records.jsonl | awk '{sum+=$1; count++} END {print "Average length:", sum/count}'
```

#### 4. Verify Source Distribution
```bash
# Count records by source
jq -r '.source' data/jsonl/records.jsonl | sort | uniq -c

# Check chemRxiv records
jq 'select(.source == "chemrxiv")' data/jsonl/records.jsonl | wc -l

# Check OpenReview records
jq 'select(.source == "openreview")' data/jsonl/records.jsonl | wc -l
```

#### 5. Validate Clean Text Files
```bash
# Check if clean text files were created
ls -la data/clean/

# Verify text extraction worked
head -n 10 data/clean/chemrxiv_*.txt
head -n 10 data/clean/openreview_*.txt
```

### Expected Output Structure

After running the scraper, you should see:

```
data/
├── jsonl/
│   └── records.jsonl          # Main output (JSONL format)
├── raw/
│   ├── chemrxiv/              # Downloaded PDFs from chemRxiv
│   └── openreview/            # Downloaded PDFs from OpenReview
├── clean/
│   ├── chemrxiv_*.txt         # Extracted text from chemRxiv PDFs
│   └── openreview_*.txt       # Extracted text from OpenReview PDFs
└── reports/
    ├── stats.csv              # Processing statistics
    ├── errors.csv             # Error log
    └── run_metrics.csv        # Performance metrics
```

### Quality Checks

1. **Record Count**: Should have records from both sources
2. **PDF Downloads**: Some records should have downloaded PDFs
3. **Text Extraction**: Clean text files should contain readable content
4. **Metadata**: Records should have titles, authors, abstracts
5. **Discussions**: OpenReview records should have discussion threads
6. **Error Rate**: Error count should be reasonable (< 10% of total)

## Troubleshooting

### Common Issues

1. **Tesseract not found**: Install Tesseract OCR and ensure it's in your PATH
2. **Playwright browser issues**: Run `playwright install chromium`
3. **Rate limiting**: Reduce `max_requests_per_minute` in config
4. **Memory issues**: Reduce `concurrency.downloads` and `concurrency.parsing`
5. **Robots.txt blocking**: Check if sites are blocking your user agent

### Debug Mode

Enable debug logging by modifying the logging level in `src/scrape/logging.py`:

```python
logger.add(sys.stderr, level="DEBUG", ...)
```

### Dry Run Mode

Use dry-run mode to test without downloading files:

```bash
python -m scrape.cli trial --config configs/trial.yaml --limit 5 --dry-run
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the error logs in `data/reports/errors.csv`
3. Open an issue on GitHub with relevant logs and configuration