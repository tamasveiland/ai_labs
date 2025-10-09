# AI Labs

Welcome to the AI Labs repository! This repository contains hands-on labs and examples for working with Azure AI services, AI Foundry, and the Microsoft AI stack.

## Overview

This repository is designed to help you learn and experiment with various Azure AI services through practical, step-by-step labs. Each lab includes complete infrastructure-as-code (Terraform) configurations and detailed instructions.

## Labs

### [Lab 01: Terraform Azure AI Foundry Environment](./labs/lab01-terraform-azure-ai-foundry/)

Learn how to provision a complete Azure AI Foundry environment using Terraform. This comprehensive lab sets up:

> 📋 **Detailed Setup Instructions**: See the [Lab 01 README](./labs/lab01-terraform-azure-ai-foundry/README.md) for complete step-by-step deployment instructions, including Terraform configuration and required manual setup steps.

**Core AI Services:**

- Azure AI Foundry Hub and Project with system-assigned managed identities
- Azure OpenAI service with GPT-4o and text-embedding-3-large deployments
- Azure AI Search with RBAC authentication and vector search capabilities
- Azure Storage with secure blob containers for documents and logs

**Security & Access:**

- Role-Based Access Control (RBAC) for all services
- Managed Identity authentication (no API keys)
- Proper role assignments for service-to-service communication
- Secure storage account with disabled shared key access

**Advanced Features:**

- Azure AI Search indexing configuration for blob storage import
- Vector search capabilities with embedding integration
- Document processing and AI enrichment pipelines
- Helper scripts for data upload and search configuration

**Technologies**: Terraform, Azure AI Foundry, Azure OpenAI, Azure AI Search, PowerShell, Bash

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

```text
ai_labs/
├── .gitignore
├── LICENSE
├── README.md
└── labs/
    └── lab01-terraform-azure-ai-foundry/
        ├── README.md                           # Lab overview and instructions
        ├── terraform/                          # Infrastructure as Code
        │   ├── .terraform.lock.hcl            # Terraform provider lock file
        │   ├── main.tf                        # Main infrastructure resources
        │   ├── variables.tf                   # Variable definitions
        │   ├── outputs.tf                     # Output values
        │   ├── provider.tf                    # Provider configurations
        │   ├── role_assignments.tf            # RBAC role assignments
        │   ├── search_indexing.tf             # Azure AI Search indexing config
        │   ├── terraform.tfvars.example       # Example variables file
        │   ├── terraform.tfvars               # Variables (gitignored)
        │   └── README.md                      # Terraform-specific documentation
        └── scripts/                           # Helper scripts
            ├── setup-blob-import.sh           # Bash script for blob import setup
            ├── Setup-BlobImport.ps1           # PowerShell script for blob import
            └── Upload-TestDocuments.ps1       # Script to upload test documents
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

These labs are for educational purposes. Be aware of the costs associated with running Azure resources and remember to clean up resources when not in use to avoid unnecessary charges.