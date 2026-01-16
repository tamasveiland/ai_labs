# Lab 03: Azure AI Evaluations - Quick Start

## One-Command Deployment

```bash
# Initialize and deploy everything
azd up
```

## Quick Commands

```bash
# Deploy infrastructure
azd provision

# View deployed resources
azd show

# Get environment variables
azd env get-values

# Load environment variables to shell
azd env refresh

# Delete all resources
azd down
```

## Local Evaluation

```bash
# Set up Python environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r evaluations/requirements.txt

# Run evaluation
cd evaluations
python evaluate_local.py
```

## GitHub Actions Setup

```bash
# Configure CI/CD pipeline
azd pipeline config

# This will:
# - Create service principal
# - Set up federated identity
# - Provide GitHub secrets
```

## Common Issues

**Q: azd command not found?**
```bash
# Install Azure Developer CLI
curl -fsSL https://aka.ms/install-azd.sh | bash  # macOS/Linux
# Or visit: https://aka.ms/install-azd
```

**Q: Deployment fails with quota error?**
- Request quota increase for Azure OpenAI in your region
- Try a different region (eastus, westus2, swedencentral)

**Q: Evaluation fails with authentication error?**
```bash
# Ensure you're logged in
az login
azd auth login

# Refresh environment variables
azd env refresh
```

## Next Steps

1. Review [README.md](./README.md) for detailed instructions
2. Explore sample RAG application in `src/`
3. Review evaluation scripts in `evaluations/`
4. Customize test data in `data/test_queries.jsonl`
5. Set up GitHub Actions with `azd pipeline config`
