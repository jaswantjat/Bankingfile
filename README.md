# Transaction Manager

An automated system for managing transactions between UnionBank's business banking platform and CloudCFO. The system automatically detects new transactions, finds matching invoices across multiple platforms, and uploads them to CloudCFO.

## Features

- Automated transaction detection from UnionBank's business banking platform
- Multi-platform invoice search (Gmail, Slack, Google Drive)
- Automatic invoice upload to CloudCFO
- Robust error handling and retry mechanisms
- Comprehensive logging and monitoring
- Rate limiting and quota management

## Prerequisites

- Python 3.8+
- Playwright
- SQLAlchemy
- Google API credentials
- Slack API token
- UnionBank credentials
- CloudCFO credentials

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Playwright browsers:
   ```bash
   playwright install
   ```

## Configuration

Create a `.env` file in the project root with the following variables:

```env
# Database
DATABASE_URL=sqlite:///transactions.db

# UnionBank
UNIONBANK_USERNAME=your_username
UNIONBANK_PASSWORD=your_password
UNIONBANK_URL=https://example.com

# API Keys
GMAIL_API_KEY=your_gmail_api_key
SLACK_API_KEY=your_slack_api_key
DRIVE_API_KEY=your_drive_api_key

# CloudCFO
CLOUDCFO_URL=https://cloudcfo.example.com
CLOUDCFO_USERNAME=your_username
CLOUDCFO_PASSWORD=your_password

# Monitoring
LOG_LEVEL=INFO
ALERT_EMAIL=alerts@example.com

# Rate Limiting
API_RATE_LIMIT=100
RETRY_MAX_ATTEMPTS=3
RETRY_INITIAL_DELAY=1.0
```

## Usage

Run the transaction manager:

```bash
python -m src.main
```

The system will:
1. Check for new transactions every 15 minutes
2. Search for matching invoices across configured platforms
3. Upload found invoices to CloudCFO
4. Log all operations and errors

## Project Structure

```
transaction-manager/
├── src/
│   ├── main.py              # Main orchestrator
│   ├── models.py            # Database models
│   ├── scrapers/
│   │   └── unionbank.py     # UnionBank scraper
│   └── services/
│       ├── invoice_finder.py    # Invoice search service
│       └── cloudcfo_uploader.py # CloudCFO upload service
├── config/
│   └── config.py            # Configuration settings
├── tests/                   # Test files
├── logs/                    # Log files
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Error Handling

The system implements comprehensive error handling:
- Automatic retries for transient failures
- Error logging with stack traces
- Error notifications via email
- Transaction status tracking
- Failed transaction recovery

## Monitoring

- All operations are logged to `logs/transaction_manager.log`
- Log rotation is configured for 500MB files
- Critical errors trigger email alerts
- Transaction processing statistics are available in the database

## Security

- Credentials are stored in environment variables
- Secure handling of sensitive data
- No hardcoded secrets
- HTTPS for all external communications

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
