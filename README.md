# Rhône Risk Policy Analysis API

A FastAPI microservice for automated cyber insurance policy analysis using Claude AI.

## Features

- **Webhook Integration**: Receive notifications when policies are uploaded to your SaaS platform
- **PDF Text Extraction**: Extract and parse policy documents using pdfplumber
- **Claude-Powered Analysis**: Comprehensive policy scoring using Rhône Risk's proprietary methodology
- **Branded PDF Reports**: Generate professional reports with maturity scores and recommendations
- **Async Processing**: Background analysis with status polling and webhook callbacks

## Quick Start

### 1. Clone and Configure

```bash
# Copy environment template
cp .env.example .env

# Add your Anthropic API key
# Edit .env and set ANTHROPIC_API_KEY=sk-ant-api03-...
```

### 2. Run with Docker Compose

```bash
docker-compose up --build
```

### 3. Verify Installation

```bash
# Run test script
chmod +x scripts/test_api.sh
./scripts/test_api.sh

# Or check manually
curl http://localhost:8000/health
```

### 4. Test with a Policy PDF

```bash
# Using the demo script
python scripts/demo_analysis.py ./sample_policy.pdf "Acme Corp" "MSP/Technology Services"

# Or via curl
curl -X POST "http://localhost:8000/analysis/upload" \
  -F "file=@policy.pdf" \
  -F "client_name=Test Client" \
  -F "client_industry=MSP/Technology Services"
```

## API Endpoints

### Health & Status

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with configuration status |
| `/` | GET | API info and version |
| `/docs` | GET | Interactive API documentation (Swagger) |

### Webhooks (for SaaS Integration)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/webhook/policy-uploaded` | POST | Receive policy upload notifications |
| `/webhook/test` | POST | Test webhook connectivity |

### Direct Analysis

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analysis/upload` | POST | Upload PDF for direct analysis |
| `/analysis/{id}/status` | GET | Check analysis progress |
| `/analysis/{id}/report` | GET | Download generated PDF report |
| `/analysis/` | GET | List all analyses |

## Webhook Payload Format

When integrating with your SaaS platform, send this payload to `/webhook/policy-uploaded`:

```json
{
  "event_type": "policy.uploaded",
  "policy_id": "pol_123",
  "client_id": "client_456",
  "client_name": "Acme Corp",
  "client_industry": "MSP/Technology Services",
  "file_url": "https://s3.amazonaws.com/bucket/policy.pdf?presigned...",
  "file_name": "acme_policy_2024.pdf",
  "file_size": 1024000,
  "policy_type": "cyber",
  "renewal": false,
  "callback_url": "https://your-saas.com/api/webhooks/analysis-complete"
}
```

### Supported Industries

- MSP/Technology Services
- Healthcare
- Financial Services
- Retail/E-commerce
- Manufacturing
- Professional Services
- Education
- Other/General

## Analysis Output

The API returns structured JSON with:

- **Executive Summary**: Overall score, recommendation, critical actions
- **Coverage Analysis**: Maturity scores (0-10) for 14+ coverage categories
- **Red Flags**: Critical exclusions and gaps
- **Recommendations**: Prioritized action items

### Recommendation Levels

| Recommendation | Score Range | Meaning |
|----------------|-------------|---------|
| BIND | ≥7.0 | Strong policy, ready to bind |
| BIND WITH CONDITIONS | 5.5-6.9 | Minor gaps, address via endorsement |
| NEGOTIATE | 4.0-5.4 | Significant gaps, negotiate with carrier |
| DECLINE | <4.0 | Major deficiencies, seek alternatives |

## Project Structure

```
rhone-policy-api/
├── src/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── routes/
│   │   ├── webhook.py       # Webhook handlers
│   │   └── analysis.py      # Direct analysis endpoints
│   ├── services/
│   │   ├── pdf_extractor.py # PDF text extraction
│   │   ├── claude_analyzer.py # Claude API integration
│   │   ├── report_generator.py # PDF report creation
│   │   └── orchestrator.py  # Workflow coordination
│   └── prompts/
│       └── system_prompt.py # Scoring methodology prompt
├── scripts/
│   ├── test_api.sh          # API test script
│   └── demo_analysis.py     # Demo upload script
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Configuration

Environment variables (set in `.env`):

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API key |
| `WEBHOOK_SECRET` | No | Shared secret for webhook verification |
| `CLAUDE_MODEL` | No | Model to use (default: claude-sonnet-4-20250514) |
| `ENVIRONMENT` | No | development/staging/production |

## Development

### Run Locally (without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
cd src
uvicorn main:app --reload
```

### Run Tests

```bash
pytest tests/
```

## Deployment

### Docker

```bash
docker build -t rhone-policy-api .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=sk-... rhone-policy-api
```

### Cloud Run / ECS

The Dockerfile is optimized for serverless container platforms:
- Minimal image size (~200MB)
- Health check endpoint
- Graceful shutdown handling

## Cost Estimation

| Volume | Claude API | Infrastructure | Monthly Total |
|--------|------------|----------------|---------------|
| 100 policies | ~$50 | ~$20 | ~$70 |
| 500 policies | ~$250 | ~$50 | ~$300 |
| 2000 policies | ~$1000 | ~$150 | ~$1150 |

*Based on ~15K tokens per analysis at Claude Sonnet pricing*

## Support

For integration support or questions about the scoring methodology, contact Rhône Risk Advisory.

---

Built with FastAPI, Claude API, and ReportLab.
