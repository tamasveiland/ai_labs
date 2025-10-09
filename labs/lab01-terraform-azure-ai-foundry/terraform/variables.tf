variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "eastus"
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "rg-ai-labs"
}

variable "project_name" {
  description = "Project name used for naming resources"
  type        = string
  default     = "ailabs"
}

variable "environment" {
  description = "Environment name (dev, test, prod)"
  type        = string
  default     = "dev"
}

variable "gpt_model_name" {
  description = "Name of the GPT model to deploy"
  type        = string
  default     = "gpt-4o"
}

variable "gpt_model_version" {
  description = "Version of the GPT model to deploy"
  type        = string
  default     = "2024-08-06"
}

variable "gpt_deployment_capacity" {
  description = "Capacity for the GPT model deployment"
  type        = number
  default     = 10
}

variable "embedding_model_name" {
  description = "Name of the embedding model to deploy"
  type        = string
  default     = "text-embedding-3-large"
}

variable "embedding_model_version" {
  description = "Version of the embedding model to deploy"
  type        = string
  default     = "1"
}

variable "embedding_deployment_capacity" {
  description = "Capacity for the embedding model deployment"
  type        = number
  default     = 10
}

variable "search_sku" {
  description = "SKU for Azure AI Search"
  type        = string
  default     = "basic"
}

variable "storage_account_tier" {
  description = "Storage account performance tier"
  type        = string
  default     = "Standard"
}

variable "storage_account_replication_type" {
  description = "Storage account replication type"
  type        = string
  default     = "LRS"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Environment = "dev"
    Project     = "AI Labs"
    ManagedBy   = "Terraform"
  }
}
