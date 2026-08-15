#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Заливка датасета Olist в локальный PostgreSQL — один раз, дальше он служит все 13 недель.

КАК ЗАПУСТИТЬ
-------------
1. pip install psycopg2-binary
2. Скачать датасет с Kaggle (olistbr/brazilian-ecommerce), распаковать zip в папку.
3. Вписать ниже пароль от Postgres и путь к папке с CSV.
4. python load_olist.py

Скрипт можно запускать сколько угодно раз: таблицы пересоздаются с нуля.
"""

import os
import sys
import time

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    sys.exit("Не установлен psycopg2. Выполните:  pip install psycopg2-binary")

# ────────────────────────────────────────────────────────────────────
#  НАСТРОЙКИ — правится только этот блок
# ────────────────────────────────────────────────────────────────────
CSV_DIR  = r"C:\olist"          # папка, куда распаковали архив с Kaggle
DB_NAME  = "olist"
HOST     = "localhost"
PORT     = 5432
USER     = "postgres"
PASSWORD = "ВАШ_ПАРОЛЬ"         # тот, что задали при установке PostgreSQL
# ────────────────────────────────────────────────────────────────────

# Имя файла → (имя таблицы, DDL). Типы проставлены руками намеренно:
# если залить всё текстом, недели 4 и 5 (даты, EXPLAIN) работать не будут.
TABLES = [
    ("olist_customers_dataset.csv", "customers", """
        CREATE TABLE customers (
            customer_id              text,
            customer_unique_id       text,
            customer_zip_code_prefix text,
            customer_city            text,
            customer_state           text
        )"""),

    ("olist_sellers_dataset.csv", "sellers", """
        CREATE TABLE sellers (
            seller_id              text,
            seller_zip_code_prefix text,
            seller_city            text,
            seller_state           text
        )"""),

    ("product_category_name_translation.csv", "category_translation", """
        CREATE TABLE category_translation (
            product_category_name         text,
            product_category_name_english text
        )"""),

    ("olist_products_dataset.csv", "products", """
        CREATE TABLE products (
            product_id                 text,
            product_category_name      text,
            product_name_lenght        int,
            product_description_lenght int,
            product_photos_qty         int,
            product_weight_g           int,
            product_length_cm          int,
            product_height_cm          int,
            product_width_cm           int
        )"""),

    ("olist_orders_dataset.csv", "orders", """
        CREATE TABLE orders (
            order_id                      text,
            customer_id                   text,
            order_status                  text,
            order_purchase_timestamp      timestamp,
            order_approved_at             timestamp,
            order_delivered_carrier_date  timestamp,
            order_delivered_customer_date timestamp,
            order_estimated_delivery_date timestamp
        )"""),

    ("olist_order_items_dataset.csv", "order_items", """
        CREATE TABLE order_items (
            order_id            text,
            order_item_id       int,
            product_id          text,
            seller_id           text,
            shipping_limit_date timestamp,
            price               numeric(12,2),
            freight_value       numeric(12,2)
        )"""),

    ("olist_order_payments_dataset.csv", "order_payments", """
        CREATE TABLE order_payments (
            order_id             text,
            payment_sequential   int,
            payment_type         text,
            payment_installments int,
            payment_value        numeric(12,2)
        )"""),

    ("olist_order_reviews_dataset.csv", "order_reviews", """
        CREATE TABLE order_reviews (
            review_id              text,
            order_id               text,
            review_score           int,
            review_comment_title   text,
            review_comment_message text,
            review_creation_date   timestamp,
            review_answer_timestamp timestamp
        )"""),

    ("olist_geolocation_dataset.csv", "geolocation", """
        CREATE TABLE geolocation (
            geolocation_zip_code_prefix text,
            geolocation_lat             double precision,
            geolocation_lng             double precision,
            geolocation_city            text,
            geolocation_state           text
        )"""),
]

# Индексы ставятся ПОСЛЕ загрузки — так быстрее, и заодно есть с чем
# сравнивать планы запросов на неделе 5.
INDEXES = [
    "CREATE INDEX idx_orders_customer   ON orders (customer_id)",
    "CREATE INDEX idx_orders_purchase   ON orders (order_purchase_timestamp)",
    "CREATE INDEX idx_items_order       ON order_items (order_id)",
    "CREATE INDEX idx_items_product     ON order_items (product_id)",
    "CREATE INDEX idx_items_seller      ON order_items (seller_id)",
    "CREATE INDEX idx_payments_order    ON order_payments (order_id)",
    "CREATE INDEX idx_reviews_order     ON order_reviews (order_id)",
    "CREATE INDEX idx_geo_zip           ON geolocation (geolocation_zip_code_prefix)",
]


def ensure_database():
    """Создаёт базу olist, если её ещё нет."""
    conn = psycopg2.connect(host=HOST, port=PORT, user=USER,
                            password=PASSWORD, dbname="postgres")
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
        if cur.fetchone():
            print(f"  база {DB_NAME} уже существует")
        else:
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
            print(f"  база {DB_NAME} создана")
    conn.close()


def main():
    if PASSWORD == "ВАШ_ПАРОЛЬ":
        sys.exit("Впишите пароль от PostgreSQL в переменную PASSWORD наверху файла.")

    # Сначала проверяем, что все девять файлов на месте, — до подключения к базе.
    missing = [f for f, _, _ in TABLES if not os.path.isfile(os.path.join(CSV_DIR, f))]
    if missing:
        print(f"В папке {CSV_DIR} не хватает файлов:")
        for f in missing:
            print("   -", f)
        sys.exit("\nПроверьте, что архив с Kaggle распакован именно в эту папку "
                 "(файлы должны лежать прямо в ней, без вложенной подпапки).")

    print("Подключаюсь к PostgreSQL...")
    ensure_database()

    conn = psycopg2.connect(host=HOST, port=PORT, user=USER,
                            password=PASSWORD, dbname=DB_NAME)
    conn.autocommit = False
    cur = conn.cursor()

    print("\nЗагружаю таблицы:")
    started = time.time()
    for filename, table, ddl in TABLES:
        path = os.path.join(CSV_DIR, filename)
        t0 = time.time()
        cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
        cur.execute(ddl)
        with open(path, "r", encoding="utf-8", newline="") as fh:
            cur.copy_expert(
                f"COPY {table} FROM STDIN WITH (FORMAT csv, HEADER true)", fh
            )
        cur.execute(f"SELECT count(*) FROM {table}")
        rows = cur.fetchone()[0]
        conn.commit()
        print(f"  {table:<22} {rows:>9,} строк   {time.time() - t0:5.1f} c".replace(",", " "))

    print("\nСтрою индексы...")
    for stmt in INDEXES:
        cur.execute(stmt)
    conn.commit()

    print("Собираю статистику для планировщика (ANALYZE)...")
    conn.autocommit = True
    cur.execute("ANALYZE")

    # Проверка, что данные действительно живые, а не просто залитые.
    cur.execute("""
        SELECT min(order_purchase_timestamp)::date,
               max(order_purchase_timestamp)::date,
               count(*)
        FROM orders
    """)
    d_from, d_to, n_orders = cur.fetchone()

    cur.close()
    conn.close()

    print(f"\nГотово за {time.time() - started:.0f} секунд.")
    print(f"Заказы: {n_orders} штук, период с {d_from} по {d_to}.")
    print(f"\nВ DBeaver подключайтесь к базе '{DB_NAME}' на {HOST}:{PORT}, "
          f"пользователь {USER}.")


if __name__ == "__main__":
    main()