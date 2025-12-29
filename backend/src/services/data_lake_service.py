
import os
import duckdb
import pandas as pd
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.core.data_config import DataConfig

class DataLakeService:
    """
    Service to manage the data lake using DuckDB and Parquet files.
    """
    
    def __init__(self):
        self.config = DataConfig()
        self.logger = logging.getLogger(__name__)
        self._con = None
        
        if self.config.STORAGE_TYPE == 'local':
             if not os.path.exists(self.config.DATA_LAKE_PATH):
                 try:
                     os.makedirs(self.config.DATA_LAKE_PATH)
                     self.logger.info(f"Created local data lake at {self.config.DATA_LAKE_PATH}")
                 except OSError as e:
                     self.logger.error(f"Failed to create data lake directory: {e}")

    def get_connection(self):
        if self._con:
            return self._con
            
        con = duckdb.connect(config={'memory_limit': self.config.DUCKDB_MEMORY_LIMIT})
        
        if self.config.STORAGE_TYPE == 's3':
            con.execute("INSTALL httpfs;")
            con.execute("LOAD httpfs;")
            
            if self.config.AWS_ACCESS_KEY_ID and self.config.AWS_SECRET_ACCESS_KEY:
                con.execute(f"SET s3_region='{self.config.AWS_REGION}';")
                con.execute(f"SET s3_access_key_id='{self.config.AWS_ACCESS_KEY_ID}';")
                con.execute(f"SET s3_secret_access_key='{self.config.AWS_SECRET_ACCESS_KEY}';")
                
        self._con = con
        return self._con
        
    def _get_full_path(self, filename: str) -> str:
        if self.config.STORAGE_TYPE == 's3':
            base = self.config.DATA_LAKE_PATH.rstrip('/')
            return f"{base}/{filename}"
        else:
            # Check if filename already includes the path or is relative
            if os.path.isabs(filename):
                return filename
            # Handles 'data_lake/file.parquet' vs 'file.parquet'
            # Our config DATA_LAKE_PATH includes 'src/data_lake'
            if filename.startswith('data_lake/'):
                 # It's trying to refer to the folder, but our path already has it
                 # Use just base filename
                 filename = os.path.basename(filename)
            
            return os.path.join(self.config.DATA_LAKE_PATH, filename)
            
    def save_to_lake(self, data: List[Dict], filename: str):
        if not data:
            self.logger.warning(f"No data to save for {filename}")
            return
            
        full_path = self._get_full_path(filename)
        
        try:
            df = pd.DataFrame(data)
            if 'date' in df.columns:
                 df['date'] = pd.to_datetime(df['date'])
            
            con = self.get_connection()
            con.register('df_view', df)
            
            self.logger.info(f"Saving to {full_path}...")
            con.execute(f"COPY (SELECT * FROM df_view) TO '{full_path}' (FORMAT PARQUET)")
            
            self.logger.info(f"Successfully saved {len(data)} records to {full_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save data to {filename}: {str(e)}")
            raise

    def query(self, query: str) -> List[Dict]:
        try:
            # We need to replace 'data_lake/' in queries with the absolute path
            # DuckDB SQL needs full paths if not in cwd
            
            # Simple replacement hack for migration
            # query = query.replace("'data_lake/", f"'{self.config.DATA_LAKE_PATH}/")
            # Wait, regex is safer, or just assuming structure
            
            if "'data_lake/" in query:
                query = query.replace("'data_lake/", f"'{self.config.DATA_LAKE_PATH}/")
            
            con = self.get_connection()
            result = con.execute(query).fetchdf()
            return result.to_dict(orient='records')
        except Exception as e:
            self.logger.error(f"Query failed: {str(e)}")
            return []

    def get_file_info(self) -> List[Dict]:
        files = []
        if self.config.STORAGE_TYPE == 'local':
            if not os.path.exists(self.config.DATA_LAKE_PATH):
                return []
            for f in os.listdir(self.config.DATA_LAKE_PATH):
                if f.endswith('.parquet'):
                    fp = os.path.join(self.config.DATA_LAKE_PATH, f)
                    try:
                        stats = os.stat(fp)
                        files.append({
                            'filename': f,
                            'size_mb': round(stats.st_size / (1024 * 1024), 2),
                            'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                            'modified_ts': stats.st_mtime
                        })
                    except OSError:
                        pass
        else:
            self.logger.warning("File listing for S3 not yet implemented")
        return files
