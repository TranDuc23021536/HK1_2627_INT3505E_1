BEGIN TRANSACTION;
CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
        );
INSERT INTO "orders" VALUES(1,'Ban phim co',2,'pending');
INSERT INTO "orders" VALUES(2,'Chuot khong day',1,'pending');
INSERT INTO "orders" VALUES(3,'Man hinh 24 inch',3,'pending');
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('orders',3);
COMMIT;