import csv
import logging
from typing import List
from ..domain.ports import InventoryRepository
from ..domain.models import LegacyProduct

# Configure logging for bad records
logging.basicConfig(
    filename='ingestion_errors.log', 
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class CsvMessageTranslator:
    """
    Pattern: Message Translator.
    Translates external CSV row format to internal Domain Model.
    """
    @staticmethod
    def to_domain(row: dict) -> LegacyProduct:
        try:
            # Flexible key matching (stripping spaces)
            safe_row = {k.strip(): v.strip() for k, v in row.items() if k}
            
            pid = safe_row.get('product_id')
            raw_stock = safe_row.get('stock')
            
            if not pid:
                raise ValueError("Missing 'product_id'")
            if not raw_stock:
                raise ValueError("Missing 'stock'")
                
            stock = int(raw_stock)
            if stock < 0:
                raise ValueError("Stock cannot be negative")
                
            return LegacyProduct(product_id=pid, stock=stock)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Transformation failed: {e}")

class IngestFileUseCase:
    def __init__(self, repository: InventoryRepository):
        self.repository = repository
        self.translator = CsvMessageTranslator()

    def execute(self, file_path: str):
        print(f" [Ingestion] Processing file: {file_path}")
        valid_products = []
        errors_count = 0
        
        try:
            with open(file_path, mode='r', encoding='utf-8-sig') as csv_file:
                # encoding='utf-8-sig' handles BOM if present from Excel
                reader = csv.DictReader(csv_file)
                
                # Validation: Columns
                if not reader.fieldnames:
                    print(" [!] Empty file or no headers")
                    return

                # Normalize headers for check
                headers = [h.strip() for h in reader.fieldnames]
                if 'product_id' not in headers or 'stock' not in headers:
                    msg = f"Invalid Columns: {headers}. Expected 'product_id', 'stock'"
                    print(f" [!] {msg}")
                    logging.error(f"File {file_path}: {msg}")
                    return

                for row_num, row in enumerate(reader, start=2): # 1 is header
                    try:
                        product = self.translator.to_domain(row)
                        valid_products.append(product)
                    except ValueError as e:
                        errors_count += 1
                        error_msg = f"Row {row_num}: {e} | Data: {row}"
                        logging.error(f"File {file_path} - {error_msg}")
                        # Don't stop process, just log ("The show must go on")
        
            if valid_products:
                print(f" [Ingestion] Upserting {len(valid_products)} records to DB...")
                self.repository.upsert_bulk(valid_products)
                print(f" [Ingestion] Success. Errors found: {errors_count}")
            else:
                print(" [Ingestion] No valid records found.")

        except Exception as e:
            print(f" [!] Critical error processing file: {e}")
            logging.error(f"Critical error {file_path}: {e}")
