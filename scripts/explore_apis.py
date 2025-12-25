#!/usr/bin/env python3
"""
API Data Exploration Script for WorldInsights.

This script tests live API connections and explores available data from
each implemented data source.

Usage:
    python scripts/explore_apis.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.infrastructure.api_clients.worldbank import WorldBankClient
from app.core.logging import setup_logging, get_logger
from app.core.config import Config


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def explore_worldbank():
    """Explore World Bank API data."""
    print_section("WORLD BANK API")
    
    client = WorldBankClient()
    
    # Test 1: Fetch countries
    print("📍 Fetching countries...")
    countries, error = client.get_countries(per_page=10)
    
    if error:
        print(f"❌ Error: {error}")
        return
    
    print(f"✅ Successfully fetched {len(countries)} countries (showing first 10)")
    print("\nSample countries:")
    for country in countries[:5]:
        print(f"  - {country['code']}: {country['name']} ({country['region']})")
    
    # Test 2: Fetch indicators
    print("\n📊 Fetching indicators...")
    indicators, error = client.get_indicators(per_page=10)
    
    if error:
        print(f"❌ Error: {error}")
        return
    
    print(f"✅ Successfully fetched {len(indicators)} indicators (showing first 10)")
    print("\nSample indicators:")
    for indicator in indicators[:5]:
        print(f"  - {indicator['code']}: {indicator['name']}")
    
    # Test 3: Fetch actual data
    print("\n📈 Fetching GDP data for USA (2015-2020)...")
    data, error = client.get_data(
        country_code='USA',
        indicator_code='NY.GDP.MKTP.CD',  # GDP (current US$)
        start_year=2015,
        end_year=2020
    )
    
    if error:
        print(f"❌ Error: {error}")
        return
    
    print(f"✅ Successfully fetched {len(data)} data points")
    print("\nData (normalized schema):")
    for record in data[:5]:
        value_str = f"${record['value']:,.0f}" if record['value'] else "N/A"
        print(f"  - {record['year']}: {value_str}")
    
    # Test 4: Fetch population data
    print("\n👥 Fetching Population data for multiple countries (2020)...")
    countries_to_test = ['USA', 'CHN', 'IND', 'GBR', 'DEU']
    
    for country_code in countries_to_test:
        data, error = client.get_data(
            country_code=country_code,
            indicator_code='SP.POP.TOTL',  # Population, total
            start_year=2020,
            end_year=2020
        )
        
        if error:
            print(f"  ❌ {country_code}: {error}")
            continue
        
        if data and data[0]['value']:
            pop = data[0]['value']
            print(f"  ✅ {country_code}: {pop:,.0f} people")
        else:
            print(f"  ⚠️  {country_code}: No data available")
    
    # Test 5: Data quality check
    print("\n🔍 Data Quality Check...")
    test_data, error = client.get_data('USA', 'NY.GDP.MKTP.CD', start_year=2010, end_year=2020)
    
    if not error and test_data:
        total_records = len(test_data)
        records_with_values = len([r for r in test_data if r['value'] is not None])
        completeness = (records_with_values / total_records) * 100
        
        print(f"  Total records: {total_records}")
        print(f"  Records with values: {records_with_values}")
        print(f"  Data completeness: {completeness:.1f}%")
        
        # Check schema compliance
        schema_valid = all(
            all(key in record for key in ['country', 'year', 'indicator', 'value', 'source'])
            for record in test_data
        )
        print(f"  Schema compliance: {'✅ PASS' if schema_valid else '❌ FAIL'}")


def main():
    """Main exploration function."""
    # Setup logging
    config = Config()
    logger = setup_logging(config)
    
    print("\n" + "🌍" * 40)
    print("  WorldInsights API Data Exploration")
    print("🌍" * 40)
    
    try:
        # Explore World Bank API
        explore_worldbank()
        
        print("\n" + "=" * 80)
        print("✅ Exploration complete!")
        print("=" * 80 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Exploration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Exploration failed: {str(e)}", exc_info=True)
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
