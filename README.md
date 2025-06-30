# ArXiv Social Good AI Paper Fetcher

An automated system for discovering and cataloging research papers related to AI bias, fairness, and social good from arXiv.org. This tool uses GPT-4o to intelligently filter papers for social impact and automatically updates a target repository with newly discovered relevant research.

## 🎯 Features

- **Intelligent Paper Detection**: Uses GPT-4o to analyze paper titles and abstracts for social good and fairness relevance
- **Automated Daily Updates**: Runs daily via GitHub Actions to fetch the latest papers
- **Historical Paper Collection**: Can fetch and process papers from the past 2 years
- **GitHub Integration**: Automatically updates target repository README with new findings
- **Comprehensive Filtering**: Focuses on AI/ML categories most likely to contain social impact research
- **Social Good Focus**: Identifies bias and fairness research across healthcare, education, criminal justice, and more
- **Reverse Chronological Order**: Always maintains newest papers at the top of README for easy access

## 🔧 Setup & Configuration

### Prerequisites

- Python 3.11+
- OpenAI API key with GPT-4o access
- GitHub Personal Access Token with repository write permissions

### Environment Variables

Configure the following environment variables:

```bash
OPENAI_API_KEY=your_openai_api_key_here
TARGET_REPO_TOKEN=your_github_token_here
TARGET_REPO_NAME=username/repository-name
```

For GitHub Actions, these should be configured as repository secrets:
- `OPENAI_API_KEY`
- `TARGET_REPO_TOKEN`

### Installation

1. Clone this repository:
```bash
git clone https://github.com/YurenHao0426/PaperFetcher.git
cd PaperFetcher
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## 🚀 Usage

### Daily Paper Fetching

Fetch papers from the last 24 hours:
```bash
python scripts/fetch_papers.py
```

Fetch papers from the last N days:
```bash
FETCH_DAYS=7 python scripts/fetch_papers.py
```

### Historical Paper Fetching

Fetch papers from the past 2 years:
```bash
FETCH_MODE=historical python scripts/fetch_papers.py
```

### Testing

Test the daily fetching functionality:
```bash
python scripts/test_daily_fetch.py
```

Test the historical fetching functionality:
```bash
python scripts/test_historical_fetch.py
```

Test the Social Good prompt effectiveness:
```bash
python scripts/test_social_good_prompt.py
```

Test the reverse chronological ordering:
```bash
python scripts/test_reverse_chronological.py
```

### Debugging

If the system completes too quickly or you suspect no papers are being fetched, use the debug script:
```bash
python scripts/debug_fetch.py
```

This will show detailed information about:
- arXiv API connectivity
- OpenAI API connectivity  
- Number of papers fetched at each step
- Sample papers and filtering results

### Parallel Processing

The system now supports parallel processing of OpenAI requests for faster filtering:

```bash
# Test parallel vs sequential performance
python scripts/test_parallel_processing.py
```

**Performance optimization options:**
```bash
# Enable/disable parallel processing
USE_PARALLEL=true python scripts/fetch_papers.py

# Control concurrent requests (default: 16 for daily, 25 for historical)
MAX_CONCURRENT=20 python scripts/fetch_papers.py

# Disable parallel processing for debugging
USE_PARALLEL=false python scripts/fetch_papers.py
```

**Expected speedup:** 3-10x faster processing depending on the number of papers and network conditions.

## 🤖 GitHub Actions

The project includes automated GitHub Actions workflows:

### Daily Schedule
- Runs daily at 12:00 UTC
- Fetches papers from the last 24 hours
- Updates target repository automatically

### Manual Trigger
- Can be triggered manually from GitHub Actions tab
- Supports both `daily` and `historical` modes
- Configurable number of days for daily mode

## 📋 Paper Categories

The system searches these arXiv categories for relevant papers:

- `cs.AI` - Artificial Intelligence
- `cs.CL` - Computation and Language  
- `cs.CV` - Computer Vision and Pattern Recognition
- `cs.LG` - Machine Learning
- `cs.NE` - Neural and Evolutionary Computing
- `cs.RO` - Robotics
- `cs.IR` - Information Retrieval
- `cs.HC` - Human-Computer Interaction
- `stat.ML` - Machine Learning (Statistics)

## 🎯 Relevance Criteria

Papers are considered relevant if they discuss:

- **Bias and fairness** in AI/ML systems with societal impact
- **Algorithmic fairness** in healthcare, education, criminal justice, hiring, or finance
- **Demographic bias** affecting marginalized or underrepresented groups
- **Data bias** and its social consequences
- **Ethical AI** and responsible AI deployment in society
- **AI safety** and alignment with human values and social welfare
- **Bias evaluation, auditing, or mitigation** in real-world applications
- **Representation and inclusion** in AI systems and datasets
- **Social implications** of AI bias (e.g., perpetuating inequality)
- **Fairness** in recommendation systems, search engines, or content moderation

## 📁 Project Structure

```
PaperFetcher/
├── scripts/
│   ├── fetch_papers.py              # Main fetching script (with parallel support)
│   ├── test_daily_fetch.py          # Daily fetching test
│   ├── test_historical_fetch.py     # Historical fetching test
│   ├── test_parallel_processing.py  # Parallel processing performance test
│   ├── test_improved_fetch.py       # Improved fetching logic test
│   ├── test_social_good_prompt.py   # Social Good prompt testing
│   ├── test_reverse_chronological.py # Reverse chronological order testing
│   └── debug_fetch.py               # Debug and troubleshooting script
├── .github/
│   └── workflows/
│       └── daily_papers.yml         # GitHub Actions workflow
├── requirements.txt                 # Python dependencies
└── README.md                       # This file
```

## 🔍 How It Works

1. **Paper Retrieval**: Queries arXiv API for papers in relevant CS categories
2. **Date Filtering**: Filters papers based on submission/update dates
3. **AI Analysis**: Uses GPT-4o to analyze each paper's title and abstract for social good relevance
4. **Social Impact Assessment**: Evaluates papers for bias, fairness, and societal implications
5. **Repository Update**: Adds relevant papers to target repository's README in reverse chronological order
6. **Version Control**: Commits changes with descriptive commit messages

## ⚙️ Configuration Options

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o | - | Yes |
| `TARGET_REPO_TOKEN` | GitHub token for repository access | - | Yes |
| `TARGET_REPO_NAME` | Target repository (owner/repo format) | `YurenHao0426/awesome-llm-bias-papers` | No |
| `FETCH_MODE` | Mode: `daily` or `historical` | `daily` | No |
| `FETCH_DAYS` | Number of days to fetch (daily mode) | `1` | No |

## 🐛 Troubleshooting

### Common Issues

1. **API Rate Limits**: The system includes retry logic and respects API limits
2. **Large Historical Fetches**: Historical mode processes up to 5000 papers and may take time
3. **Token Permissions**: Ensure GitHub token has write access to target repository

### Debugging

Enable debug logging by modifying the logging level in the script:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 📧 Contact

For questions or issues, please open a GitHub issue or contact the maintainer.

---

**Note**: This tool is designed for academic research purposes. Please respect arXiv's usage policies and OpenAI's API terms of service.