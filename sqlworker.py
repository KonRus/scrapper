import sqlite3
from typing import List
from listing import Listing

DB_NAME = "listings.db"

def init_database():
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS listings (
                    listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    page VARCHAR(15) NULL,
                    title VARCHAR(255) NULL,
                    price INTEGER,
                    city VARCHAR(15) NULL,
                    district VARCHAR(50) NULL,
                    area REAL NULL,
                    url VARCHAR(255) NULL
                )
            ''')
            conn.commit()
            print(f"Database {DB_NAME} initialized successfully")
            
    except sqlite3.Error as e:
        print(f"Error creating database: {e}")
        raise

class DatabaseWorker:
    def __init__(self):
        self.db_name = DB_NAME
        self.existing_records = {}  # {(page, title): listing_id}
        self._init_cache()
    
    def _init_cache(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT listing_id, page, title FROM listings')
            for listing_id, page, title in cursor.fetchall():
                self.existing_records[(page, title)] = listing_id
    
    def upsert_listings(self, listings: List[Listing], source: str):
        updates = []
        inserts = []
        
        for listing in listings:
            if (source, listing.title) in self.existing_records:
                updates.append((
                    listing.price, 
                    listing.city, 
                    listing.district, 
                    listing.area,
                    listing.url,
                    self.existing_records[(source, listing.title)]
                ))
            else:
                inserts.append((
                    source,
                    listing.title,
                    listing.price,
                    listing.city,
                    listing.district,
                    listing.area,
                    listing.url
                ))
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                
                # Process updates
                if updates:
                    cursor.executemany('''
                        UPDATE listings 
                        SET price = ?, city = ?, district = ?, area = ?, url = ?
                        WHERE listing_id = ?
                    ''', updates)
                
                # Process inserts
                if inserts:
                    cursor.executemany('''
                        INSERT INTO listings (page, title, price, city, district, area, url)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', inserts)
                    
                    # Update cache with new records
                    for listing in listings:
                        if (source, listing.title) not in self.existing_records:
                            cursor.execute('''
                                SELECT listing_id FROM listings 
                                WHERE page = ? AND title = ?
                            ''', (source, listing.title))
                            listing_id = cursor.fetchone()[0]
                            self.existing_records[(source, listing.title)] = listing_id
                
                conn.commit()
        except sqlite3.Error as e:
            print(f"An error occurred while puting the data into database: {e}")
            pass
        finally:
            print(f"Updated {len(updates)} and inserted {len(inserts)} listings from {source}")
