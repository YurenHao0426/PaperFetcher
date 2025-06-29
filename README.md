# ArXiv LLM Bias Paper Fetcher

An automated system for discovering and cataloging research papers related to bias in Large Language Models (LLMs) from arXiv.org. This tool uses GPT-4o to intelligently filter papers and automatically updates a target repository with newly discovered relevant research.

## 🎯 Features

- **Intelligent Paper Detection**: Uses GPT-4o to analyze paper titles and abstracts for LLM bias relevance
- **Automated Daily Updates**: Runs daily via GitHub Actions to fetch the latest papers
- **Historical Paper Collection**: Can fetch and process papers from the past 2 years
- **GitHub Integration**: Automatically updates target repository README with new findings
- **Comprehensive Filtering**: Focuses on AI/ML categories most likely to contain relevant research

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

Test the historical fetching functionality:
```bash
python scripts/test_historical_fetch.py
```

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

- Bias in large language models, generative AI, or foundation models
- Fairness issues in NLP models or text generation
- Ethical concerns with language models
- Demographic bias in AI systems
- Alignment and safety of language models
- Bias evaluation or mitigation in NLP

## 📁 Project Structure

```
PaperFetcher/
├── scripts/
│   ├── fetch_papers.py          # Main fetching script
│   ├── test_historical_fetch.py # Historical fetching test
│   └── [other test scripts]     # Legacy test scripts
├── .github/
│   └── workflows/
│       └── daily_papers.yml     # GitHub Actions workflow
├── requirements.txt             # Python dependencies
└── README.md                   # This file
```

## 🔍 How It Works

1. **Paper Retrieval**: Queries arXiv API for papers in relevant CS categories
2. **Date Filtering**: Filters papers based on submission/update dates
3. **AI Analysis**: Uses GPT-4o to analyze each paper's title and abstract
4. **Repository Update**: Adds relevant papers to target repository's README
5. **Version Control**: Commits changes with descriptive commit messages

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