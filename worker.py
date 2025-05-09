import time
from extract.fetch_coingecko import fetch_bitcoin_price
from load.dlq_handler import handle_dlq
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)


def insert_price_record(timestamp, price):
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO prices (timestamp, price)
                VALUES (:timestamp, :price)
            """),
            {"timestamp": timestamp, "price": price}
        )


def run_etl():
    while True:
        print("🔄 Running ETL cycle...")
        payload = fetch_bitcoin_price()

        if payload is None:
            print("⚠️ Skipping due to fetch error.")
            time.sleep(60)
            continue
        payload["price"] = "NOT_A_NUMBER"
        try:
            insert_price_record(payload["timestamp"], payload["price"])
            print(f"✅ Inserted price: ${payload['price']} at {payload['timestamp']}")
        except Exception as e:
            print("❌ Failed to insert into DB, sending to DLQ.")
            handle_dlq(payload, str(e))

        time.sleep(60)  # Wait 1 minute


if __name__ == "__main__":
    run_etl()