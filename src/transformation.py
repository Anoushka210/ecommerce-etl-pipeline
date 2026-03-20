from pyspark.sql import functions as F


def aggregate_payments(payments):
    # Some orders have multiple payments (e.g. voucher + credit card)
    # Collapse them into one row per order with total value
    return payments.groupBy("order_id").agg(
        F.sum("payment_value").alias("total_payment"),
        F.count("payment_sequential").alias("payment_count"),
        F.first("payment_type").alias("primary_payment_type")
    )


def aggregate_items(items):
    # Some orders have multiple products
    # Collapse into one row per order
    return items.groupBy("order_id").agg(
        F.sum("price").alias("items_subtotal"),
        F.sum("freight_value").alias("total_freight"),
        F.count("order_item_id").alias("item_count")
    )


def join_tables(orders, customers, payments_agg, items_agg):
    df = orders \
        .join(customers, "customer_id", "left") \
        .join(payments_agg, "order_id", "left") \
        .join(items_agg, "order_id", "left")

    # Cache in memory — this DataFrame is reused across all aggregations
    # so caching avoids recomputing the joins multiple times
    df = df.cache()

    # Repartition for optimised parallel writes
    df = df.repartition(8)

    return df


def engineer_features(df):
    # How many days it took to deliver
    df = df.withColumn(
        "delivery_time_days",
        F.datediff(
            F.col("order_delivered_customer_date"),
            F.col("order_purchase_timestamp")
        )
    )

    # Was the order delivered late vs estimated?
    df = df.withColumn(
        "delivery_delay_days",
        F.datediff(
            F.col("order_delivered_customer_date"),
            F.col("order_estimated_delivery_date")
        )
    )

    # Positive = late, Negative = early
    df = df.withColumn(
        "was_late",
        F.when(F.col("delivery_delay_days") > 0, True).otherwise(False)
    )

    # Bucket orders by total payment value
    df = df.withColumn(
        "order_value_bucket",
        F.when(F.col("total_payment") < 50,   "low")
         .when(F.col("total_payment") < 200,  "medium")
         .when(F.col("total_payment") < 500,  "high")
         .otherwise("premium")
    )

    # Extract month and year for trend analysis
    df = df.withColumn("purchase_year",
                       F.year("order_purchase_timestamp"))
    df = df.withColumn("purchase_month",
                       F.month("order_purchase_timestamp"))

    return df


def run_transformation(orders, customers, payments, items):
    print("\n--- Transformation Summary ---")

    payments_agg = aggregate_payments(payments)
    items_agg    = aggregate_items(items)

    print(f"  Payments collapsed: {payments_agg.count()} unique orders")
    print(f"  Items collapsed:    {items_agg.count()} unique orders")

    master = join_tables(orders, customers, payments_agg, items_agg)
    master = engineer_features(master)

    print(f"  Master table rows:  {master.count()}")
    print(f"  Master table cols:  {len(master.columns)}")
    print(f"\n  Columns: {master.columns}")
    print("--- Transformation Complete ---\n")

    return master


if __name__ == "__main__":
    from ingestion import create_spark_session, load_raw_data
    from cleaning import run_cleaning

    spark = create_spark_session()
    orders, customers, payments, items = load_raw_data(spark, "data/raw")
    orders, customers, payments, items = run_cleaning(orders, customers,
                                                      payments, items)
    run_transformation(orders, customers, payments, items)