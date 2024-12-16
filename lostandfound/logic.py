import sqlite3
import numpy as np
import cv2
import os

DATABASE = 'store.db'

class StoreManager:
    def __init__(self, database):
        self.database = database
        self.create_tables()

    def create_tables(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS items (
                                item_id INTEGER PRIMARY KEY,
                                name TEXT NOT NULL,
                                date TEXT,
                                img TEXT
                            )''')
            conn.commit()

    def add_items(self, name, img, date):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute("INSERT INTO items (name, date, img) VALUES (?, ?, ?)", (name, date, img))
            conn.commit()

    def date_selector(self, date):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM items WHERE date = ? AND (julianday('now') - julianday(date)) <= 3", (date,))
            return cur.fetchall()

    def get_items(self):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM items")
            return cur.fetchall()
        
    def get_items_data(self, item_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM items WHERE item_id = ?", (item_id,))
            return cur.fetchone()

    def delete_item(self, item_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT img FROM items WHERE item_id = ?", (item_id,))
            result = cur.fetchone()
            img_path = result[0] if result else None
            cur.execute("DELETE FROM items WHERE item_id = ?", (item_id,))
            conn.commit()
        if img_path and os.path.exists(img_path):
            try:
                os.remove(img_path)
            except FileNotFoundError:
                pass
    
    def collage_creation(self, paths, output):
        images = []
        for path in paths:
            img = cv2.imread(path)
            if img is None:
                print(f"Warning: Unable to read {path}. It may not exist or is corrupted.")
                continue
            images.append(cv2.resize(img, (200, 200)))

        if not images:
            print("No valid images to create a collage.")
            return
        
        if len(images) == 1:
            collage = images[0]
        elif len(images) == 2:
            collage = np.vstack(images)
        elif len(images) == 3:
            collage = np.hstack(images[:3])
        else:
            col1 = np.hstack(images[:2])
            col2 = np.hstack(images[2:])
            collage = np.vstack([col1, col2])

        cv2.imwrite(output, collage)

if __name__ == '__main__':
    manager = StoreManager(DATABASE)
    manager.collage_creation(["img/666.jpg", "img/745.jpg", "img/745.jpg", "img/745.jpg"], "output.png")
