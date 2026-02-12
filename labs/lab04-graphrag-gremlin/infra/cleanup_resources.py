#!/usr/bin/env python3
"""
Cleanup Azure resources for GraphRAG lab.

This script deletes the entire resource group and all resources within it.
"""

import sys
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from config import Config

def main():
    """Main cleanup function."""
    print("\n" + "=" * 80)
    print("GraphRAG Infrastructure Cleanup")
    print("=" * 80)
    
    # Load configuration
    config = Config()
    
    print(f"\nResource Group to delete: {config.resource_group_name}")
    print(f"Location: {config.location}")
    
    # Confirm deletion
    response = input("\n⚠️  WARNING: This will delete ALL resources in the resource group.\n"
                    "Are you sure you want to continue? (yes/no): ")
    
    if response.lower() != 'yes':
        print("Cleanup cancelled.")
        sys.exit(0)
    
    # Get Azure credentials
    print("\n🔐 Authenticating with Azure...")
    try:
        credential = DefaultAzureCredential()
        resource_client = ResourceManagementClient(credential, config.subscription_id)
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        print("\nPlease run 'az login' to authenticate with Azure.")
        sys.exit(1)
    
    # Delete resource group
    try:
        print(f"\n🗑️  Deleting resource group: {config.resource_group_name}")
        print("This may take several minutes...")
        
        delete_async = resource_client.resource_groups.begin_delete(
            config.resource_group_name
        )
        
        delete_async.wait()
        
        print("\n" + "=" * 80)
        print("✅ Cleanup Complete!")
        print("=" * 80)
        print(f"\nDeleted resource group: {config.resource_group_name}")
        print("All resources have been removed.\n")
        
    except Exception as e:
        if "ResourceGroupNotFound" in str(e):
            print(f"\n✓ Resource group '{config.resource_group_name}' does not exist.")
        else:
            print(f"\n❌ Cleanup failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    main()
