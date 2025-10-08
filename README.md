# AI Labs

Welcome to the AI Labs repository! This repository contains hands-on labs and examples for working with Azure AI services, AI Foundry, and the Microsoft AI stack.

## Overview

This repository is designed to help you learn and experiment with various Azure AI services through practical, step-by-step labs. Each lab includes complete infrastructure-as-code (Terraform) configurations and detailed instructions.

## Labs

### [Lab 01: Terraform Azure AI Foundry Environment](./labs/lab01-terraform-azure-ai-foundry/)

Learn how to provision a complete Azure AI Foundry environment using Terraform. This lab sets up:

- Azure AI Foundry Hub and Project
- Azure OpenAI with GPT-4o deployment
- Azure AI Search for RAG scenarios
- Azure Storage for data and artifacts
- Supporting infrastructure (Key Vault, Application Insights, Container Registry)

**Technologies**: Terraform, Azure AI Foundry, Azure OpenAI, Azure AI Search

## Prerequisites

To work with these labs, you'll need:

- An active Azure subscription
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) installed
- [Terraform](https://www.terraform.io/downloads.html) >= 1.5.0
- Basic knowledge of Azure services
- Appropriate permissions to create resources in your Azure subscription

## Getting Started

1. Clone this repository:
   ```bash
   git clone https://github.com/tamasveiland/ai_labs.git
   cd ai_labs
   ```

2. Navigate to a lab directory:
   ```bash
   cd labs/lab01-terraform-azure-ai-foundry
   ```

3. Follow the README instructions in the lab directory

## Repository Structure

```
ai_labs/
├── labs/
│   └── lab01-terraform-azure-ai-foundry/
│       ├── README.md
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       ├── terraform.tf
│       └── terraform.tfvars.example
├── LICENSE
└── README.md
```

## Contributing

Contributions are welcome! If you have ideas for new labs or improvements to existing ones, please feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Resources

- [Azure AI Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-studio/)
- [Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Azure AI Search](https://learn.microsoft.com/en-us/azure/search/)
- [Terraform Azure Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)

## Disclaimer

These labs are for educational purposes. Be aware of the costs associated with running Azure resources and remember to clean up resources when you're done experimenting.