#!/usr/bin/env python3
"""Test the enhanced categorization logic."""

from config import Config

def test_categorization_logic():
    """Test that the category filtering logic is configured correctly."""
    config = Config()
    
    print("Email Categorization Setup")
    print("=" * 60)
    print(f"Available categories: {', '.join(config.EMAIL_CATEGORIES)}")
    print(f"Categories to KEEP: {', '.join(config.CATEGORIES_TO_KEEP)}")
    print()
    
    print("Processing Logic:")
    print("-" * 60)
    
    for category in config.EMAIL_CATEGORIES:
        if category in config.CATEGORIES_TO_KEEP:
            action = f"✓ KEEP - Will be labeled '{category}' and archived"
        else:
            action = f"✗ DELETE - Will be moved to trash"
        print(f"{category:15} → {action}")
    
    print("-" * 60)
    print()
    print("Summary:")
    print(f"  • {len(config.CATEGORIES_TO_KEEP)} categories will be saved")
    print(f"  • {len(config.EMAIL_CATEGORIES) - len(config.CATEGORIES_TO_KEEP)} categories will be deleted")
    print()
    print("To customize, set environment variable CATEGORIES_TO_KEEP:")
    print("  export CATEGORIES_TO_KEEP='Notes,Github,Primary'")

if __name__ == '__main__':
    test_categorization_logic()
