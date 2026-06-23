import os
import time
import re
import unicodedata
import sqlite3
from collections import defaultdict
from flask import Flask, request, jsonify, send_from_directory

DATABASE = "alobook.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Create leads table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            price TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT
        )
    ''')
    
    # Create orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            customer TEXT NOT NULL,
            total TEXT NOT NULL,
            items TEXT NOT NULL,
            shipping_address TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create escalations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS escalations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp REAL NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    ''')
    
    conn.commit()
    
    # Seed products if empty
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        products = [
            (1, "Nhà Giả Kim", "Paulo Coelho", "79,000 VND", "Kỹ năng sống", "Một cuốn sách triết lý sâu sắc về việc theo đuổi ước mơ."),
            (2, "Đắc Nhân Tâm", "Dale Carnegie", "86,000 VND", "Phát triển bản thân", "Sách gối đầu giường của mọi thời đại về nghệ thuật giao tiếp và thu phục lòng người."),
            (3, "Đọc Vị Bất Kỳ Ai", "David J. Lieberman", "95,000 VND", "Tâm lý học", "Để không bị lừa dối và lợi dụng, hiểu thấu tâm lý người đối diện."),
            (4, "Sách Cho Người Mới Đi Làm", "Nhiều tác giả", "120,000 VND", "Kinh doanh", "Kỹ năng làm việc hiệu quả, thích nghi nhanh với môi trường công sở."),
            (5, "Đầu Tư Tài Chính", "Zvi Bodie", "350,000 VND", "Tài chính", "Kiến thức hàn lâm chuyên sâu về thị trường chứng khoán và quản lý danh mục đầu tư."),
            (6, "Tư Duy Nhanh Và Chậm", "Daniel Kahneman", "180,000 VND", "Tâm lý học", "Cuốn sách kinh điển phân tích hai hệ thống tư duy quyết định hành vi con người."),
            (7, "Cha Giàu Cha Nghèo", "Robert Kiyosaki", "98,000 VND", "Tài chính", "Bài học giá trị về quản lý tài chính cá nhân và tư duy làm giàu."),
            (8, "Hạt Giống Tâm Hồn", "Nhiều tác giả", "68,000 VND", "Kỹ năng sống", "Những câu chuyện ngắn đầy ý nghĩa và nghị lực vươn lên trong cuộc sống.")
        ]
        cursor.executemany("INSERT INTO products (id, title, author, price, category, description) VALUES (?, ?, ?, ?, ?, ?)", products)
        conn.commit()
        
    # Seed orders if empty
    cursor.execute("SELECT COUNT(*) FROM orders")
    if cursor.fetchone()[0] == 0:
        orders = [
            ("AB12345", "paid", "Nguyen Van A", "250,000 VND", "Nhà Giả Kim", "123 Nguyen Trai, Q.5, TP.HCM"),
            ("AB67890", "shipping", "Tran Thi B", "420,000 VND", "Đắc Nhân Tâm, Đọc Vị Bất Kỳ Ai", "456 Le Loi, Q.1, TP.HCM"),
            ("AB11223", "pending", "Le Van C", "180,000 VND", "Sách Cho Người Mới Đi Làm", "789 CMT8, Q.10, TP.HCM"),
            ("AB44556", "delivered", "Pham Minh D", "310,000 VND", "Đầu Tư Tài Chính", "321 Dien Bien Phu, Q. Bình Thạnh, TP.HCM"),
            ("AB77889", "cancelled", "Hoang Thi E", "95,000 VND", "Đọc Vị Bất Kỳ Ai", "147 Ly Tu Trong, Q.1, TP.HCM"),
            ("AB99001", "refunded", "Vu Van F", "86,000 VND", "Đắc Nhân Tâm", "963 Tran Hung Dao, Q.5, TP.HCM"),
            ("AB22334", "returning", "Ngo Thi G", "158,000 VND", "Nhà Giả Kim, Đắc Nhân Tâm", "159 Ba Thang Hai, Q.10, TP.HCM"),
            ("AB33445", "shipping", "Nguyen Thi H", "180,000 VND", "Tư Duy Nhanh Và Chậm", "789 Phan Chu Trinh, Đà Nẵng"),
            ("AB55667", "paid", "Tran Van I", "278,000 VND", "Cha Giàu Cha Nghèo, Tư Duy Nhanh Và Chậm", "321 Tran Phu, Nha Trang")
        ]
        cursor.executemany("INSERT INTO orders (order_id, status, customer, total, items, shipping_address) VALUES (?, ?, ?, ?, ?, ?)", orders)
        conn.commit()
        
    conn.close()

# Initialize DB on import/startup
init_db()

def remove_accents(input_str: str) -> str:
    nfd_form = unicodedata.normalize('NFD', input_str)
    temp = u"".join([c for c in nfd_form if unicodedata.category(c) != 'Mn'])
    return temp.replace('đ', 'd').replace('Đ', 'D')

def extract_and_save_lead(message: str):
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", message, re.IGNORECASE)
    phone_match = re.search(r"(0|\+84)[0-9]{9}\b", message)
    
    if email_match and phone_match:
        email = email_match.group(0)
        phone = phone_match.group(0)
        
        name = "Khách hàng Chat"
        name_match = re.search(r"(?:tên\s+là|tôi\s+là|tên\s+tôi\s+là)\s+([A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝĂĐĨŨƠƯa-zàáâãèéêìíòóôõùúýăđĩũơư\s]{2,30})", message, re.IGNORECASE)
        if name_match:
            name = name_match.group(1).strip()
        else:
            email_prefix = email.split('@')[0]
            name = email_prefix.replace('.', ' ').replace('_', ' ').title()
            
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM leads WHERE email = ? OR phone = ?", (email, phone))
        exists = cursor.fetchone()
        if not exists:
            cursor.execute("INSERT INTO leads (name, email, phone) VALUES (?, ?, ?)", (name, email, phone))
            conn.commit()
            print(f"[Lead Auto-Extract] Extracted and saved lead: {name} | {email} | {phone}")
        conn.close()

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Rate limiter setup: 10 messages per 60 seconds per IP
rate_limit_records = defaultdict(list)
RATE_LIMIT_MAX = 10
RATE_LIMIT_WINDOW = 60 # seconds

def check_rate_limit(ip: str) -> bool:
    current_time = time.time()
    # Filter out requests older than 60 seconds
    rate_limit_records[ip] = [t for t in rate_limit_records[ip] if current_time - t < RATE_LIMIT_WINDOW]
    if len(rate_limit_records[ip]) >= RATE_LIMIT_MAX:
        return False
    rate_limit_records[ip].append(current_time)
    return True

# Serving index.html directly on root
@app.route("/")
def get_index():
    return app.send_static_file('index.html')

# Serving admin.html directly on /admin
@app.route("/admin")
def get_admin():
    return app.send_static_file('admin.html')

# CORS Header helper (since flask_cors is not installed to keep dependencies minimal)
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response

# Handle preflight options requests
@app.route("/api/<path:path>", methods=["OPTIONS"])
def handle_options(path):
    return "", 200

# API Endpoints
@app.route("/api/leads", methods=["POST"])
def create_lead():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    
    if not name or not email or not phone:
        return jsonify({"detail": "Vui lòng nhập đầy đủ Tên, Email và Số điện thoại."}), 400
        
    # Email check
    if not re.match(r"^[\w.+-]+@[\w-]+\.[a-z]{2,}$", email, re.IGNORECASE):
        return jsonify({"detail": "Định dạng email không hợp lệ."}), 400
        
    # Phone check
    if not re.match(r"^(0|\+84)[0-9]{9}$", phone):
        return jsonify({"detail": "Định dạng số điện thoại không hợp lệ (cần 10 chữ số bắt đầu bằng 0 hoặc +84)."}), 400
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO leads (name, email, phone) VALUES (?, ?, ?)", (name, email, phone))
    conn.commit()
    conn.close()
    
    print(f"[Lead Gen] New lead recorded: {name} ({email})")
    return jsonify({"status": "success", "message": "Thông tin liên hệ của bạn đã được ghi nhận."})

@app.route("/api/orders/<order_id>", methods=["GET"])
def get_order(order_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE UPPER(order_id) = ?", (order_id.upper().strip(),))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({"detail": "Không tìm thấy mã đơn hàng này. Vui lòng kiểm tra lại."}), 404
        
    order = dict(row)
    order["items"] = [x.strip() for x in order["items"].split(",")]
    return jsonify(order)

@app.route("/api/products/search", methods=["GET"])
def search_products():
    q = request.args.get("q", "").strip()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    if not q:
        return jsonify(products)
        
    q_clean = remove_accents(q.lower())
    q_words = q_clean.split()
    
    results = []
    for product in products:
        target_text = f"{product['title']} {product['description']} {product['category']}".lower()
        target_clean = remove_accents(target_text)
        if all(word in target_clean for word in q_words):
            results.append(product)
    return jsonify(results)

@app.route("/api/chat/escalate", methods=["POST"])
def escalate_chat():
    data = request.get_json() or {}
    session_id = data.get("session_id", "default_session")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO escalations (session_id, timestamp, status) VALUES (?, ?, ?)", (session_id, time.time(), "pending"))
    conn.commit()
    conn.close()
    
    print(f"[Escalation] Session {session_id} escalated to human agent.")
    return jsonify({"status": "success", "message": "Đã chuyển phiên chat cho nhân viên hỗ trợ."})

@app.route("/api/demo/data", methods=["GET"])
def get_demo_data():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT order_id, customer, status, total FROM orders")
    orders = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({
        "products": products,
        "orders": orders
    })

# Load environment variables
from dotenv import load_dotenv
import httpx

load_dotenv()
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "https://sunbv56.app.n8n.cloud/webhook/alobook-webhook")
N8N_USERNAME = os.getenv("N8N_USERNAME")
N8N_PASSWORD = os.getenv("N8N_PASSWORD")

@app.route("/api/chat/message", methods=["POST"])
def send_message():
    # Rate limit check
    client_ip = request.remote_addr
    if not check_rate_limit(client_ip):
        return jsonify({"detail": "Bạn đã gửi quá nhiều tin nhắn. Vui lòng thử lại sau 1 phút (Tối đa 10 tin nhắn/phút)."}), 429
        
    data = request.get_json() or {}
    message = data.get("message")
    message = str(message).strip() if message is not None else ""
    session_id = data.get("session_id")
    session_id = str(session_id).strip() if session_id is not None else ""
    user_name = data.get("user_name")
    user_name = str(user_name).strip() if user_name is not None else ""
    
    msg = message.lower()
    
    # 1. Intercept order search directly from local database (supports both AB and BM prefixes)
    order_match = re.search(r"\b(AB|BM)\d{5}\b", message, re.IGNORECASE)
    if order_match:
        order_id = order_match.group(0).upper()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            order = dict(row)
            items_list = [x.strip() for x in order["items"].split(",")]
            status_vn = {
                "paid": "Đã thanh toán (Paid)",
                "shipping": "Đang giao hàng (Shipping)",
                "pending": "Chưa thanh toán (Pending)",
                "delivered": "Đã giao hàng thành công (Delivered)",
                "cancelled": "Đã hủy đơn (Cancelled)",
                "refunded": "Đã hoàn tiền (Refunded)",
                "returning": "Đang chuyển hoàn (Returning)"
            }.get(order['status'], order['status'])
            
            return jsonify({
                "reply": f"Mã đơn hàng: {order['order_id']}\nTrạng thái: {status_vn}\nKhách hàng: {order['customer']}\nSách: {', '.join(items_list)}\nĐịa chỉ: {order['shipping_address']}\nTổng thanh toán: {order['total']}"
            })
            
    # Try forwarding to production n8n webhook first
    if N8N_WEBHOOK_URL:
        try:
            print(f"[Proxy] Forwarding to n8n: {N8N_WEBHOOK_URL} (Auth: {'Yes' if N8N_USERNAME else 'No'})")
            files = {
                "message": (None, message),
                "session_id": (None, session_id),
                "user_name": (None, user_name),
                "chatId": (None, session_id),
                "order_status": (None, "")
            }
            
            auth = (N8N_USERNAME, N8N_PASSWORD) if N8N_USERNAME and N8N_PASSWORD else None
            response = httpx.post(N8N_WEBHOOK_URL, files=files, auth=auth, timeout=60.0)
            
            if response.status_code in [200, 201]:
                n8n_data = response.json()
                print(f"[Proxy] n8n response: {n8n_data}")
                
                reply_text = ""
                buttons = []
                escalated = False
                
                if isinstance(n8n_data, list) and len(n8n_data) > 0:
                    item = n8n_data[0]
                else:
                    item = n8n_data
                
                if isinstance(item, dict):
                    reply_text = item.get("output") or item.get("text") or item.get("reply") or ""
                    buttons = item.get("buttons", [])
                    escalated = item.get("escalated", False) or item.get("escalate", False)
                elif isinstance(item, str):
                    reply_text = item
                
                if not reply_text:
                    reply_text = str(item)
                
                # Save escalation if requested by user or flagged by n8n
                if escalated or "hỗ trợ" in msg or "nhân viên" in msg or "gặp người" in msg:
                    conn = get_db()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO escalations (session_id, timestamp, status) VALUES (?, ?, ?)", (session_id, time.time(), "pending"))
                    conn.commit()
                    conn.close()
                    escalated = True
                
                return jsonify({
                    "reply": reply_text,
                    "buttons": buttons,
                    "escalated": escalated
                })
            elif response.status_code == 524:
                print(f"[Proxy Warning] n8n 524 timeout")
                return jsonify({
                    "reply": "⏱️ Hệ thống AI đang xử lý hơi lâu. Vui lòng thử lại sau vài giây, hoặc hỏi tôi câu khác nhé!"
                })
            else:
                print(f"[Proxy Warning] n8n responded with status {response.status_code}")
                return jsonify({
                    "reply": f"⚠️ Không thể kết nối đến AI lúc này (lỗi {response.status_code}). Vui lòng thử lại sau."
                })
        except httpx.TimeoutException:
            print(f"[Proxy Error] n8n webhook timed out")
            return jsonify({
                "reply": "⏱️ AI đang bận xử lý, phản hồi hơi chậm. Bạn vui lòng thử lại sau vài giây nhé!"
            })
        except Exception as e:
            print(f"[Proxy Error] Failed to connect to n8n webhook: {str(e)}")
            # Fall back to local mock
 
    # Rule-based fallback replies for local testing
    if "đơn hàng" in msg or "giao hàng" in msg:
        return jsonify({
            "reply": "Để tra cứu đơn hàng, vui lòng nhập mã đơn hàng của bạn (Ví dụ: AB12345) hoặc click nút 'Vận chuyển & Giao hàng' bên dưới.",
            "buttons": [{"label": "Vận chuyển & Giao hàng", "value": "check_order"}]
        })
    elif "sách" in msg or "tìm sách" in msg:
        return jsonify({
            "reply": "Tôi có thể giúp bạn tìm các sách phù hợp. Bạn muốn tìm sách thể loại gì? (Ví dụ: kỹ năng sống, kinh doanh...)",
            "buttons": [{"label": "Tìm kiếm sách", "value": "search_books"}]
        })
    elif "hỗ trợ" in msg or "nhân viên" in msg or "gặp người" in msg:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO escalations (session_id, timestamp, status) VALUES (?, ?, ?)", (session_id, time.time(), "pending"))
        conn.commit()
        conn.close()
        return jsonify({
            "reply": "Tôi đang chuyển bạn gặp nhân viên hỗ trợ. Vui lòng đợi trong giây lát... 🕒",
            "escalated": True
        })
    
    # Check if this matches an order search directly
    match = re.search(r"AB\d{5}", message, re.IGNORECASE)
    if match:
        order_id = match.group(0).upper()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            order = dict(row)
            items_list = [x.strip() for x in order["items"].split(",")]
            status_vn = {
                "paid": "Đã thanh toán (Paid)",
                "shipping": "Đang giao hàng (Shipping)",
                "pending": "Chưa thanh toán (Pending)",
                "delivered": "Đã giao hàng thành công (Delivered)",
                "cancelled": "Đã hủy đơn (Cancelled)",
                "refunded": "Đã hoàn tiền (Refunded)",
                "returning": "Đang chuyển hoàn (Returning)"
            }.get(order['status'], order['status'])
            
            return jsonify({
                "reply": f"Mã đơn hàng: {order['order_id']}\nTrạng thái: {status_vn}\nKhách hàng: {order['customer']}\nSách: {', '.join(items_list)}\nĐịa chỉ: {order['shipping_address']}\nTổng thanh toán: {order['total']}"
            })
    
    return jsonify({
        "reply": f"Chào {user_name or 'bạn'}! Tôi là AI Sales Assistant của AloBook. Tôi đã nhận được tin nhắn: '{message}'. (Lưu ý: n8n webhook tại cloud đang ngoại tuyến hoặc chưa kích hoạt, đây là phản hồi tự động từ Localhost)."
    })

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

@app.route("/api/admin/data", methods=["GET"])
def get_admin_data():
    req_pass = request.headers.get("X-Admin-Password")
    if req_pass != ADMIN_PASSWORD:
        return jsonify({"detail": "Unauthorized. Incorrect admin password."}), 401
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads ORDER BY id DESC")
    leads = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM escalations ORDER BY id DESC")
    escalations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({
        "leads": leads,
        "escalations": escalations
    })

@app.route("/api/admin/escalations/<int:id>/resolve", methods=["POST"])
def resolve_escalation(id):
    req_pass = request.headers.get("X-Admin-Password")
    if req_pass != ADMIN_PASSWORD:
        return jsonify({"detail": "Unauthorized. Incorrect admin password."}), 401
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE escalations SET status = 'resolved' WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    print(f"[Admin] Escalation ID {id} marked as resolved.")
    return jsonify({"status": "success", "message": f"Escalation {id} resolved."})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
