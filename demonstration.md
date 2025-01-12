# Transaction Manager System Demonstration

## 1. System Architecture (5 minutes)

### Key Components:
- **UnionBank Scraper** (`src/scrapers/unionbank.py`)
  - Uses Playwright for web automation
  - Periodically checks for new transactions
  - Extracts transaction details (amount, date, vendor)

- **Invoice Finder** (`src/services/invoice_finder.py`)
  - Searches across multiple platforms:
    - Gmail (using Google API)
    - Slack (using Slack API)
    - Google Drive (using Drive API)
  - Falls back to vendor portals if needed

- **Portal Scraper** (`src/services/portal_scraper.py`)
  - Handles vendor portal automation
  - Configurable for different portals
  - Secure credential management

- **CloudCFO Uploader** (`src/services/cloudcfo_uploader.py`)
  - Automated invoice upload
  - Web UI interaction
  - Error handling

## 2. Live Demonstration (15 minutes)

### Step 1: Initialize System
```bash
# Start the system
python demo.py
```

Watch as the system:
1. Initializes the database
2. Sets up API connections
3. Starts the monitoring service

### Step 2: Transaction Detection
- Show UnionBank login process
- Display detected transactions
- Explain transaction filtering

### Step 3: Invoice Search
Demonstrate invoice finding across:
1. Gmail search
2. Slack search
3. Drive search
4. Portal fallback

### Step 4: CloudCFO Upload
- Show the upload process
- Demonstrate error handling
- View success confirmation

## 3. Security Features (5 minutes)

### Credential Management
- Environment variables
- No hardcoded secrets
- Secure token handling

### Error Handling
- Comprehensive logging
- Error tracking
- Automatic retries

## 4. Monitoring & Maintenance (5 minutes)

### Health Check
```bash
# Start the health check server
uvicorn src.health:app --reload
```

### Logs & Metrics
- Transaction success rate
- Processing time
- Error patterns

## 5. Q&A Session (10 minutes)

## Running the Demo

1. **Prerequisites**:
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Install Playwright browsers
   playwright install
   ```

2. **Configuration**:
   - Copy `.env.example` to `.env`
   - Add your credentials:
     - UnionBank login
     - Gmail API key
     - Slack token
     - CloudCFO credentials

3. **Start the Demo**:
   ```bash
   python demo.py
   ```

4. **Monitor Health**:
   ```bash
   uvicorn src.health:app --reload
   ```

## Key Features to Highlight

1. **Automation**:
   - No manual intervention needed
   - Periodic checking
   - Smart invoice matching

2. **Reliability**:
   - Multiple search methods
   - Fallback mechanisms
   - Error recovery

3. **Security**:
   - Secure credential storage
   - API key management
   - Audit logging

4. **Scalability**:
   - Easy to add new portals
   - Configurable checking frequency
   - Performance monitoring

## Common Questions & Answers

1. **How often does it check for transactions?**
   - Configurable, default is every 15 minutes

2. **What happens if an invoice isn't found?**
   - Multiple search attempts
   - Portal fallback
   - Error notification

3. **How secure are the credentials?**
   - Environment variables
   - No hardcoding
   - Encrypted storage

4. **Can we add more portals?**
   - Yes, through portal configurations
   - No code changes needed
   - Easy to maintain
