
import os
import sys
import argparse
import time
import logging
from datetime import datetime

from app.services.data_lake_service import DataLakeService
from app.services.data_ingestion.weather import WeatherIngestor
from app.services.data_ingestion.worldbank import WorldBankIngestor
from app.services.data_ingestion.who import WhoIngestor
from app.services.data_ingestion.fao import FaoIngestor
from app.services.data_ingestion.nasa import NasaIngestor
from app.services.data_ingestion.news import NewsIngestor
from app.services.data_ingestion.stocks import StocksIngestor
from app.services.data_ingestion.geo import GeoIngestor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataManager:
    """Orchestrator for Data Lake Management."""
    
    def __init__(self):
        self.service = DataLakeService()
        self.ingestors = [
            WeatherIngestor(self.service),
            StocksIngestor(self.service),
            NewsIngestor(self.service),
            WorldBankIngestor(self.service),
            WhoIngestor(self.service),
            FaoIngestor(self.service),
            NasaIngestor(self.service),
            GeoIngestor(self.service)
        ]
        
    def check_status(self) -> bool:
        """
        Check which ingestors need updates without running them.
        Returns True if ANY update is needed (exit code 1 behaviour).
        """
        updates_needed = False
        print(f"\n{'Source':<15} | {'Interval (h)':<12} | {'Status':<15}")
        print("-" * 50)
        
        for ingestor in self.ingestors:
            needs_update = ingestor.should_update() # This logs details
            status = "NEEDS UPDATE" if needs_update else "OK"
            print(f"{ingestor.name:<15} | {ingestor.interval_hours:<12} | {status:<15}")
            if needs_update:
                updates_needed = True
                
        return updates_needed

    def run_update(self, force: bool = False, specific_source: str = None):
        """Run update for ingestors."""
        results = []
        
        targets = self.ingestors
        if specific_source:
             targets = [i for i in self.ingestors if i.name.lower() == specific_source.lower()]
             if not targets:
                 logger.error(f"Source '{specific_source}' not found.")
                 return
        
        for ingestor in targets:
            if force or ingestor.should_update():
                try:
                    res = ingestor.ingest()
                    res['name'] = ingestor.name
                    res['timestamp'] = datetime.now()
                    results.append(res)
                except Exception as e:
                    logger.error(f"Ingestion failed for {ingestor.name}: {e}")
                    results.append({'name': ingestor.name, 'status': 'error', 'error': str(e)})
            else:
                logger.info(f"Skipping {ingestor.name} (up to date).")
                results.append({'name': ingestor.name, 'status': 'skipped'})
                
        self.update_readme(results)
        
    def update_readme(self, results):
        """Generate/Update README.md in data_lake directory."""
        if self.service.config.STORAGE_TYPE == 's3':
            # Skip readme generation on S3 for now or implement uploading
            logger.info("Skipping README generation for S3 storage.")
            return

        readme_path = os.path.join(self.service.config.DATA_LAKE_PATH, 'README.md')
        
        files_info = self.service.get_file_info()
        total_size = sum(f['size_mb'] for f in files_info)
        
        content = f"""# WorldInsights Data Lake
        
**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Size:** {total_size:.2f} MB
**Files:** {len(files_info)}

## Ingestion Status
| Source | Status | Last Run | Records | Notes |
| :--- | :--- | :--- | :--- | :--- |
"""
        for res in results:
            status = res.get('status', 'unknown')
            tstamp = datetime.now().strftime('%H:%M:%S')
            count = res.get('records_count', '-')
            notes = str(res.get('errors', ''))[:50] + "..." if res.get('errors') else ""
            if status == 'skipped':
                notes = "Up to date"
            
            content += f"| {res['name']} | {status} | {tstamp} | {count} | {notes} |\n"
            
        content += "\n## Files\n| Filename | Size (MB) | Modified |\n| :--- | :--- | :--- |\n"
        for f in files_info:
             content += f"| {f['filename']} | {f['size_mb']} | {f['modified']} |\n"
             
        try:
            with open(readme_path, 'w') as f:
                f.write(content)
            logger.info(f"Updated {readme_path}")
        except Exception as e:
            logger.error(f"Failed to update README: {e}")

    def scheduler_loop(self, interval_seconds=300):
        """Run in a loop checking for updates."""
        logger.info(f"Starting Scheduler Loop (Check every {interval_seconds}s)...")
        while True:
            logger.info("Scheduler: Checking sources...")
            self.run_update(force=False)
            logger.info("Scheduler: Sleep.")
            time.sleep(interval_seconds)

    def query(self, sql):
        results = self.service.query(sql)
        print(f"\nQuery Results ({len(results)} rows):")
        if results:
            import pandas as pd
            print(pd.DataFrame(results))
        else:
            print("No results found.")

def main():
    parser = argparse.ArgumentParser(description="WorldInsights Modular Data Manager")
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update data in the lake')
    update_parser.add_argument('--force', action='store_true', help='Force update regardless of interval')
    update_parser.add_argument('--source', type=str, help='Run specific source only')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check status validation only')
    # Scheduler command
    sched_parser = subparsers.add_parser('scheduler', help='Run as a background scheduler')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Run a SQL query')
    query_parser.add_argument('sql', type=str, help='SQL query to execute')

    args = parser.parse_args()
    
    manager = DataManager()

    if args.command == 'update':
        manager.run_update(force=args.force, specific_source=args.source)
    elif args.command == 'check':
        needs_update = manager.check_status()
        sys.exit(1 if needs_update else 0)
    elif args.command == 'scheduler':
        manager.scheduler_loop()
    elif args.command == 'query':
        if not args.sql:
            print("Please provide a SQL query.")
            return
        manager.query(args.sql)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
