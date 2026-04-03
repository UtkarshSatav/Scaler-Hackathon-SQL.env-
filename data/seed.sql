-- SQLEnv Deterministic Seed Data
-- Carefully crafted to support easy/medium/hard SQL tasks

-- ============================================================
-- CUSTOMERS (20 rows)
-- ============================================================
INSERT INTO customers (id, name, email, age, city, signup_date) VALUES
(1,  'Aarav Sharma',    'aarav@example.com',    28, 'Mumbai',      '2023-03-15'),
(2,  'Priya Patel',     'priya@example.com',    35, 'Delhi',       '2023-05-20'),
(3,  'Rahul Kumar',     'rahul@example.com',    42, 'Bangalore',   '2023-01-10'),
(4,  'Sneha Gupta',     'sneha@example.com',    24, 'Mumbai',      '2024-02-14'),
(5,  'Vikram Singh',    'vikram@example.com',   31, 'Chennai',     '2023-07-01'),
(6,  'Ananya Reddy',    'ananya@example.com',   29, 'Hyderabad',   '2023-09-05'),
(7,  'Arjun Nair',      'arjun@example.com',    38, 'Bangalore',   '2023-04-18'),
(8,  'Kavita Joshi',    'kavita@example.com',   45, 'Pune',        '2023-02-28'),
(9,  'Deepak Verma',    'deepak@example.com',   33, 'Delhi',       '2024-01-05'),
(10, 'Meera Iyer',      'meera@example.com',    27, 'Chennai',     '2023-11-12'),
(11, 'Rohan Das',       'rohan@example.com',    36, 'Kolkata',     '2023-06-22'),
(12, 'Pooja Mishra',    'pooja@example.com',    41, 'Pune',        '2023-08-15'),
(13, 'Suresh Menon',    'suresh@example.com',   50, 'Mumbai',      '2023-03-30'),
(14, 'Nisha Agarwal',   'nisha@example.com',    23, 'Delhi',       '2024-03-01'),
(15, 'Amit Pandey',     'amit@example.com',     34, 'Bangalore',   '2023-10-10'),
(16, 'Ritu Chopra',     'ritu@example.com',     30, 'Hyderabad',   '2023-12-25'),
(17, 'Karan Malhotra',  'karan@example.com',    26, 'Mumbai',      '2024-01-20'),
(18, 'Divya Saxena',    'divya@example.com',    39, 'Chennai',     '2023-05-05'),
(19, 'Nikhil Bhat',     'nikhil@example.com',   32, 'Kolkata',     '2023-07-14'),
(20, 'Swati Tiwari',    'swati@example.com',    44, 'Pune',        '2023-04-02');

-- ============================================================
-- PRODUCTS (15 rows, 4 categories)
-- ============================================================
INSERT INTO products (id, name, category, price, stock) VALUES
(1,  'Wireless Headphones',   'Electronics', 2499.00,  50),
(2,  'Smartphone Case',       'Electronics',  499.00, 200),
(3,  'Bluetooth Speaker',     'Electronics', 3999.00,  30),
(4,  'USB-C Cable',           'Electronics',  199.00, 500),
(5,  'Cotton T-Shirt',        'Clothing',     599.00, 150),
(6,  'Denim Jeans',           'Clothing',    1499.00,  80),
(7,  'Running Shoes',         'Clothing',    2999.00,  40),
(8,  'Winter Jacket',         'Clothing',    3499.00,  25),
(9,  'Python Programming',    'Books',        449.00, 100),
(10, 'Data Science Handbook',  'Books',       699.00,  60),
(11, 'Mystery Novel',          'Books',       299.00, 120),
(12, 'Cooking Recipes',        'Books',       399.00,  90),
(13, 'Ceramic Mug Set',        'Home',        799.00,  70),
(14, 'Desk Lamp',              'Home',       1299.00,  45),
(15, 'Plant Pot',              'Home',        349.00, 110);

-- ============================================================
-- ORDERS (30 rows)
-- ============================================================
INSERT INTO orders (id, customer_id, order_date, status, total_amount) VALUES
(1,  1,  '2024-01-15', 'delivered',  2998.00),
(2,  1,  '2024-03-20', 'delivered',   499.00),
(3,  2,  '2024-02-10', 'delivered',  4498.00),
(4,  3,  '2024-01-05', 'delivered',  1798.00),
(5,  3,  '2024-04-12', 'shipped',    3999.00),
(6,  2,  '2024-03-01', 'delivered',   599.00),
(7,  5,  '2024-02-28', 'delivered',  5997.00),
(8,  5,  '2024-05-15', 'shipped',    1299.00),
(9,  6,  '2024-01-20', 'delivered',   898.00),
(10, 7,  '2024-03-10', 'delivered',  2499.00),
(11, 7,  '2024-06-01', 'pending',     699.00),
(12, 8,  '2024-02-14', 'delivered',  4998.00),
(13, 8,  '2024-04-25', 'cancelled',  1499.00),
(14, 9,  '2024-03-05', 'delivered',   848.00),
(15, 10, '2024-01-30', 'delivered',  2999.00),
(16, 10, '2024-05-20', 'shipped',     449.00),
(17, 11, '2024-02-18', 'delivered',  1598.00),
(18, 12, '2024-03-22', 'delivered',  3499.00),
(19, 13, '2024-04-08', 'shipped',     798.00),
(20, 13, '2024-01-12', 'delivered',  2499.00),
(21, 11, '2024-05-01', 'pending',     599.00),
(22, 15, '2024-02-05', 'delivered',  1748.00),
(23, 15, '2024-06-10', 'pending',     299.00),
(24, 16, '2024-03-15', 'delivered',   999.00),
(25, 17, '2024-04-20', 'shipped',    2499.00),
(26, 18, '2024-01-25', 'delivered',  4498.00),
(27, 18, '2024-05-30', 'delivered',   699.00),
(28, 19, '2024-02-22', 'delivered',  1299.00),
(29, 19, '2024-06-05', 'cancelled',   399.00),
(30, 20, '2024-03-28', 'delivered',  3798.00);

-- ============================================================
-- ORDER_ITEMS (60 rows)
-- ============================================================
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES
-- Order 1: customer 1 bought headphones + smartphone case
(1,  1,  1,  1, 2499.00),
(2,  1,  2,  1,  499.00),
-- Order 2: customer 1 bought smartphone case
(3,  2,  2,  1,  499.00),
-- Order 3: customer 2 bought headphones + jeans + smartphone case
(4,  3,  1,  1, 2499.00),
(5,  3,  6,  1, 1499.00),
(6,  3,  2,  1,  499.00),
-- Order 4: customer 3 bought desk lamp + smartphone case
(7,  4,  14, 1, 1299.00),
(8,  4,  2,  1,  499.00),
-- Order 5: customer 3 bought bluetooth speaker
(9,  5,  3,  1, 3999.00),
-- Order 6: customer 2 bought t-shirt
(10, 6,  5,  1,  599.00),
-- Order 7: customer 5 bought running shoes x2
(11, 7,  7,  2, 2999.00),
-- Order 8: customer 5 bought desk lamp
(12, 8,  14, 1, 1299.00),
-- Order 9: customer 6 bought mug set + usb cable
(13, 9,  13, 1,  799.00),
(14, 9,  4,  1,  199.00),  -- total should be 998, but we set 898 for slight difference
-- Order 10: customer 7 bought headphones
(15, 10, 1,  1, 2499.00),
-- Order 11: customer 7 bought data science book
(16, 11, 10, 1,  699.00),
-- Order 12: customer 8 bought headphones x2
(17, 12, 1,  2, 2499.00),
-- Order 13: customer 8 bought jeans (cancelled)
(18, 13, 6,  1, 1499.00),
-- Order 14: customer 9 bought python book + plant pot
(19, 14, 9,  1,  449.00),
(20, 14, 15, 1,  349.00),
-- Order 15: customer 10 bought running shoes
(21, 15, 7,  1, 2999.00),
-- Order 16: customer 10 bought python book
(22, 16, 9,  1,  449.00),
-- Order 17: customer 11 bought mug set x2
(23, 17, 13, 2,  799.00),
-- Order 18: customer 12 bought winter jacket
(24, 18, 8,  1, 3499.00),
-- Order 19: customer 13 bought mug set (shipped)
(25, 19, 13, 1,  799.00),
-- Order 20: customer 13 bought headphones
(26, 20, 1,  1, 2499.00),
-- Order 21: customer 11 bought t-shirt (pending)
(27, 21, 5,  1,  599.00),
-- Order 22: customer 15 bought python book + desk lamp
(28, 22, 9,  1,  449.00),
(29, 22, 14, 1, 1299.00),
-- Order 23: customer 15 bought mystery novel (pending)
(30, 23, 11, 1,  299.00),
-- Order 24: customer 16 bought t-shirt + cooking book
(31, 24, 5,  1,  599.00),
(32, 24, 12, 1,  399.00),
-- Order 25: customer 17 bought headphones (shipped)
(33, 25, 1,  1, 2499.00),
-- Order 26: customer 18 bought bluetooth speaker + smartphone case
(34, 26, 3,  1, 3999.00),
(35, 26, 2,  1,  499.00),
-- Order 27: customer 18 bought data science book
(36, 27, 10, 1,  699.00),
-- Order 28: customer 19 bought desk lamp
(37, 28, 14, 1, 1299.00),
-- Order 29: customer 19 bought cooking book (cancelled)
(38, 29, 12, 1,  399.00),
-- Order 30: customer 20 bought running shoes + mug set
(39, 30, 7,  1, 2999.00),
(40, 30, 13, 1,  799.00);

-- ============================================================
-- REVIEWS (25 rows)
-- ============================================================
INSERT INTO reviews (id, product_id, customer_id, rating, review_text, review_date) VALUES
(1,  1,  1,  5, 'Amazing sound quality, worth every penny!',          '2024-02-01'),
(2,  1,  7,  4, 'Good headphones, battery could be better.',          '2024-03-25'),
(3,  1,  13, 5, 'Best wireless headphones I have owned.',             '2024-02-15'),
(4,  2,  1,  3, 'Decent case but feels a bit cheap.',                 '2024-04-01'),
(5,  2,  3,  4, 'Good fit, protects the phone well.',                 '2024-02-10'),
(6,  3,  18, 5, 'Incredible bass for the price!',                     '2024-02-20'),
(7,  3,  5,  4, 'Great speaker, slightly heavy though.',              '2024-06-01'),
(8,  5,  4,  4, 'Soft cotton, very comfortable.',                     '2024-03-15'),
(9,  5,  16, 3, 'Okay quality, shrunk after washing.',                '2024-04-05'),
(10, 6,  2,  5, 'Perfect fit, love the style!',                       '2024-03-10'),
(11, 7,  5,  5, 'Super comfortable for running.',                     '2024-03-20'),
(12, 7,  10, 4, 'Good shoes but sizing runs a bit large.',            '2024-02-15'),
(13, 7,  20, 5, 'Best running shoes ever!',                           '2024-04-10'),
(14, 8,  12, 4, 'Warm and stylish, great for winter.',                '2024-04-01'),
(15, 9,  9,  5, 'Excellent book for learning Python.',                '2024-04-10'),
(16, 9,  15, 4, 'Good content, some chapters feel rushed.',           '2024-03-01'),
(17, 10, 7,  3, 'Covers basics well, lacks depth on ML topics.',      '2024-06-15'),
(18, 11, 15, 4, 'Gripping plot, could not put it down!',             '2024-06-20'),
(19, 13, 6,  5, 'Beautiful mugs, great as a gift set.',               '2024-02-10'),
(20, 13, 11, 4, 'Nice mugs, one had a small chip.',                   '2024-03-05'),
(21, 13, 20, 5, 'Excellent quality ceramic.',                         '2024-04-15'),
(22, 14, 3,  4, 'Bright and adjustable, good for desk work.',         '2024-02-20'),
(23, 14, 19, 5, 'Perfect desk lamp, love the design.',                '2024-03-10'),
(24, 15, 9,  3, 'Looks nice but drainage hole is too small.',         '2024-04-15'),
(25, 12, 16, 4, 'Great recipes, easy to follow instructions.',        '2024-04-20');
