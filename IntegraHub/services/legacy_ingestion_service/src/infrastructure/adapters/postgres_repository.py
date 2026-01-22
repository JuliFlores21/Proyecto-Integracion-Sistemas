from sqlalchemy import create_engine, text
from ...domain.ports import InventoryRepository
from ...domain.models import LegacyProduct

class PostgresInventoryRepository(InventoryRepository):
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)

    def upsert_bulk(self, products: list[LegacyProduct]):
        # We assume the 'products' table exists from Inventory Service infrastructure.
        # We share the same Database in this mono-repo setup via docker-compose.
        
        with self.engine.connect() as conn:
            for p in products:
                # UPSERT Logic (PostgreSQL specific)
                # If product exists -> Add stock (Replenishment logic)
                stmt = text("""
                    INSERT INTO products (product_id, stock) 
                    VALUES (:pid, :stock)
                    ON CONFLICT (product_id) 
                    DO UPDATE SET stock = products.stock + EXCLUDED.stock;
                """)
                conn.execute(stmt, {"pid": p.product_id, "stock": p.stock})
            conn.commit()
