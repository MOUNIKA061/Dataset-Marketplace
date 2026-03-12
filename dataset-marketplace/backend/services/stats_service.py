# ============================================================================
# Dataset Marketplace - Statistics Service
# Data analysis and statistics calculations for visualization
# ============================================================================

import pandas as pd
import numpy as np
import json
import io
from typing import Dict, List, Any, Optional


class StatsService:
    """
    Service for calculating dataset statistics and preparing
    data for frontend visualization.
    
    Provides:
    - Basic statistics (mean, median, min, max, std)
    - Column type detection
    - Data preview generation
    - Aggregation for charts
    """
    
    def __init__(self):
        """Initialize statistics service."""
        pass
    
    def parse_file(self, file_data: bytes, file_type: str) -> Optional[pd.DataFrame]:
        """
        Parse file data into pandas DataFrame.
        
        Args:
            file_data: Raw file bytes
            file_type: File extension (csv, json, xlsx)
        
        Returns:
            pd.DataFrame: Parsed data frame
            None: If parsing fails
        """
        try:
            # Create file-like object from bytes
            file_buffer = io.BytesIO(file_data)
            
            # Parse based on file type
            if file_type.lower() == 'csv':
                # Parse CSV with automatic delimiter detection
                df = pd.read_csv(file_buffer, encoding='utf-8', on_bad_lines='skip')
            
            elif file_type.lower() == 'json':
                # Try to parse as JSON (array of objects or records format)
                try:
                    df = pd.read_json(file_buffer, orient='records')
                except ValueError:
                    # Try other orientations
                    file_buffer.seek(0)
                    df = pd.read_json(file_buffer)
            
            elif file_type.lower() in ['xlsx', 'xls']:
                # Parse Excel file
                df = pd.read_excel(file_buffer)
            
            else:
                # Unsupported file type
                return None
            
            return df
        
        except Exception as e:
            # Log error and return None
            print(f"Error parsing file: {str(e)}")
            return None
    
    def get_column_info(self, df: pd.DataFrame) -> List[Dict[str, str]]:
        """
        Extract column names and data types from DataFrame.
        
        Args:
            df: pandas DataFrame
        
        Returns:
            list: List of dicts with column name, type, and nullable info
                  [{'name': 'col1', 'type': 'float64', 'nullable': True}, ...]
        """
        column_info = []
        
        for col in df.columns:
            # Get pandas dtype
            dtype = str(df[col].dtype)
            
            # Map to simplified type names
            if 'int' in dtype:
                simple_type = 'integer'
            elif 'float' in dtype:
                simple_type = 'decimal'
            elif 'datetime' in dtype:
                simple_type = 'datetime'
            elif 'bool' in dtype:
                simple_type = 'boolean'
            else:
                simple_type = 'text'
            
            # Check for null values
            has_nulls = df[col].isnull().any()
            
            column_info.append({
                'name': str(col),
                'type': simple_type,
                'original_type': dtype,
                'nullable': bool(has_nulls)
            })
        
        return column_info
    
    def generate_snippet(self, df: pd.DataFrame, max_rows: int = 100) -> str:
        """
        Generate JSON snippet from first N rows of DataFrame.
        
        Args:
            df: pandas DataFrame
            max_rows: Maximum number of rows to include
        
        Returns:
            str: JSON string representation of data
        """
        # Limit to max_rows
        preview_df = df.head(max_rows)
        
        # Handle NaN values (convert to None for JSON)
        preview_df = preview_df.replace({np.nan: None})
        
        # Convert DataFrame to list of dicts
        records = preview_df.to_dict(orient='records')
        
        # Convert to JSON string
        return json.dumps(records, default=str)
    
    def calculate_basic_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate basic statistics for all numeric columns.
        
        Args:
            df: pandas DataFrame
        
        Returns:
            dict: Statistics for each numeric column
                  {
                      'column_name': {
                          'count': N,
                          'mean': float,
                          'median': float,
                          'min': float,
                          'max': float,
                          'std': float,
                          'q25': float,  # 25th percentile
                          'q75': float   # 75th percentile
                      }
                  }
        """
        stats = {}
        
        # Get numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            # Get column data excluding NaN
            col_data = df[col].dropna()
            
            if len(col_data) == 0:
                continue
            
            # Calculate statistics
            stats[col] = {
                'count': int(len(col_data)),
                'mean': float(col_data.mean()),
                'median': float(col_data.median()),
                'min': float(col_data.min()),
                'max': float(col_data.max()),
                'std': float(col_data.std()) if len(col_data) > 1 else 0,
                'q25': float(col_data.quantile(0.25)),
                'q75': float(col_data.quantile(0.75))
            }
        
        return stats
    
    def get_visualization_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Prepare data for frontend chart visualization.
        
        Args:
            df: pandas DataFrame
        
        Returns:
            dict: Visualization-ready data
                  {
                      'numeric_stats': {...},
                      'histograms': {...},
                      'value_counts': {...},
                      'summary': {...}
                  }
        """
        result = {
            'numeric_stats': {},
            'histograms': {},
            'value_counts': {},
            'summary': {
                'row_count': len(df),
                'column_count': len(df.columns)
            }
        }
        
        # Get basic stats for numeric columns
        result['numeric_stats'] = self.calculate_basic_stats(df)
        
        # Generate histogram data for numeric columns (limited to first 5)
        numeric_cols = df.select_dtypes(include=[np.number]).columns[:5]
        for col in numeric_cols:
            col_data = df[col].dropna()
            if len(col_data) > 0:
                # Create histogram with 10 bins
                counts, bin_edges = np.histogram(col_data, bins=10)
                result['histograms'][col] = {
                    'counts': counts.tolist(),
                    'bin_edges': bin_edges.tolist(),
                    'labels': [f"{bin_edges[i]:.2f}-{bin_edges[i+1]:.2f}" 
                               for i in range(len(counts))]
                }
        
        # Get value counts for categorical columns (limited to first 5)
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns[:5]
        for col in categorical_cols:
            # Get top 10 most common values
            value_counts = df[col].value_counts().head(10)
            result['value_counts'][col] = {
                'labels': value_counts.index.tolist(),
                'counts': value_counts.values.tolist()
            }
        
        return result
    
    def get_column_stats(self, df: pd.DataFrame, column_name: str) -> Dict[str, Any]:
        """
        Get detailed statistics for a specific column.
        
        Args:
            df: pandas DataFrame
            column_name: Name of column to analyze
        
        Returns:
            dict: Detailed column statistics
        """
        if column_name not in df.columns:
            return {'error': f'Column {column_name} not found'}
        
        col_data = df[column_name]
        dtype = str(col_data.dtype)
        
        stats = {
            'name': column_name,
            'type': dtype,
            'total_count': len(col_data),
            'null_count': int(col_data.isnull().sum()),
            'unique_count': int(col_data.nunique())
        }
        
        # Add numeric-specific stats
        if np.issubdtype(col_data.dtype, np.number):
            clean_data = col_data.dropna()
            stats.update({
                'mean': float(clean_data.mean()) if len(clean_data) > 0 else None,
                'median': float(clean_data.median()) if len(clean_data) > 0 else None,
                'min': float(clean_data.min()) if len(clean_data) > 0 else None,
                'max': float(clean_data.max()) if len(clean_data) > 0 else None,
                'std': float(clean_data.std()) if len(clean_data) > 1 else None
            })
        else:
            # Categorical stats
            top_values = col_data.value_counts().head(5)
            stats['top_values'] = dict(zip(
                [str(x) for x in top_values.index.tolist()],
                top_values.values.tolist()
            ))
        
        return stats
    
    def aggregate_data(self, df: pd.DataFrame, group_by: str, 
                       agg_column: str, agg_func: str = 'sum') -> Dict[str, Any]:
        """
        Aggregate data for chart visualization.
        
        Args:
            df: pandas DataFrame
            group_by: Column to group by
            agg_column: Column to aggregate
            agg_func: Aggregation function (sum, mean, count, min, max)
        
        Returns:
            dict: Aggregated data ready for charting
                  {'labels': [...], 'values': [...]}
        """
        # Validate columns exist
        if group_by not in df.columns:
            return {'error': f'Column {group_by} not found'}
        if agg_column not in df.columns and agg_func != 'count':
            return {'error': f'Column {agg_column} not found'}
        
        # Perform aggregation
        try:
            if agg_func == 'count':
                grouped = df.groupby(group_by).size()
            else:
                grouped = df.groupby(group_by)[agg_column].agg(agg_func)
            
            # Convert to chart-ready format
            return {
                'labels': grouped.index.tolist(),
                'values': grouped.values.tolist(),
                'group_by': group_by,
                'aggregation': f'{agg_func}({agg_column})'
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def correlation_matrix(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate correlation matrix for numeric columns.
        
        Args:
            df: pandas DataFrame
        
        Returns:
            dict: Correlation matrix data
                  {'columns': [...], 'matrix': [[...]]}
        """
        # Get numeric columns
        numeric_df = df.select_dtypes(include=[np.number])
        
        if numeric_df.empty:
            return {'error': 'No numeric columns found'}
        
        # Calculate correlation matrix
        corr_matrix = numeric_df.corr()
        
        return {
            'columns': corr_matrix.columns.tolist(),
            'matrix': corr_matrix.values.tolist()
        }


# Global instance
stats_service = StatsService()
