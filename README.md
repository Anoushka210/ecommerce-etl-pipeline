# E-Commerce Sales Analytics ETL Pipeline

## Architecture Diagram
```mermaid
flowchart LR
    A[Kaggle CSVsorders, customers, payments, items] --> B[IngestionPySpark DataFrames]
    B --> C[CleaningNulls, deduplication, filtering]
    C --> D[TransformationJoins + feature engineering]
    D --> E[AggregationBusiness metrics and KPIs]
    E --> F1[ParquetOptimized storage]
    E --> F2[CSV ReportsAnalytics outputs]
    F1 --> G[DownstreamML and Analytics]
    F2 --> G
```

An end-to-end PySpark ETL pipeline built on the Brazilian E-Commerce
Public Dataset (Olist) with 100k+ orders across multiple relational tables.

## Project Structure
```
ecommerce_etl/
├── data/
│   ├── raw/          # Source CSVs from Kaggle
│   ├── output/       # Parquet + CSV outputs
├── src/
│   ├── ingestion.py       # Loads CSVs into Spark DataFrames
│   ├── cleaning.py        # Null handling, deduplication, filtering
│   ├── transformation.py  # Joins, feature engineering
│   ├── aggregation.py     # Business-level aggregations
│   └── main.py            # Orchestrates full pipeline
└── notebooks/
    └── exploration.ipynb  # Initial data exploration
```

## Dataset

Brazilian E-Commerce Public Dataset by Olist — available on Kaggle.
Place the CSV files in `data/raw/` before running.

- 99,441 orders
- 99,441 customers
- 103,886 payments
- 112,650 order items

## Pipeline Stages

**1. Ingestion** — Loads 4 CSV files into PySpark DataFrames with
schema inference.

**2. Cleaning**
- Drops rows with null critical fields (order_id, customer_id)
- Removes duplicate orders
- Filters to delivered orders only
- Removes zero-value payments
- Result: 96,478 clean orders

**3. Transformation**
- Aggregates payments per order (handles split payments)
- Aggregates items per order (handles multi-item orders)
- Joins orders + customers + payments + items into master table
- Engineers features:
  - `delivery_time_days` — actual days taken to deliver
  - `delivery_delay_days` — days vs estimated delivery date
  - `was_late` — boolean flag for late deliveries
  - `order_value_bucket` — low / medium / high / premium
  - `purchase_year`, `purchase_month` — for trend analysis

**4. Aggregation**
- Revenue by state (total, count, average order value)
- Monthly sales trend (2016–2018)
- Delivery performance by state (avg days, late %)
- Order value distribution by bucket

**5. Output**
- Master cleaned dataset saved as Parquet
- All aggregation reports saved as CSV

## Key Findings

- São Paulo (SP) leads with R$5.77M revenue across 40,501 orders
- SP also has the fastest average delivery at 8.7 days
- 63% of orders fall in the medium value bucket (R$50–200)
- Average late delivery rate across all states is under 10%
- Business grew from 265 orders in Oct 2016 to 1,653 in Feb 2017

## How to Run
```bash
# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate       # Mac/Linux
venv\Scripts\activate          # Windows

# 2. Install dependencies
pip install pyspark pandas pyarrow jupyter

# 3. Add Kaggle CSVs to data/raw/

# 4. Run full pipeline
python src/main.py
```

## Tools Used

- Python 3.10
- PySpark 3.x — distributed data processing
- Pandas — data exploration
- PyArrow — Parquet file support
- Jupyter — initial data exploration