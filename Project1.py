from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
import sqlite3
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key"  # ใช้สำหรับ flash message

# ฟังก์ชันสำหรับเชื่อมต่อและสร้างตารางผู้ใช้ในฐานข้อมูล
def init_db():
    conn = sqlite3.connect("user.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prefix TEXT NOT NULL,
            studentID TEXT NOT NULL UNIQUE,
            firstName TEXT NOT NULL,
            lastName TEXT NOT NULL,
            year INTEGER NOT NULL,
            department TEXT NOT NULL,
            accountNumber TEXT NOT NULL,
            age INTEGER NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL,
            password TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            book_id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_name TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()

def hash_password(value):
    return hashlib.sha256(value.encode()).hexdigest()

def verify_user(studentID, password):
    with sqlite3.connect("user.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password FROM users WHERE studentID = ?", 
            (studentID,)
        )
        user = cursor.fetchone()
        if user and hash_password(password) == user[0]:
            return True  # ถ้ารหัสผ่านถูกต้อง
        return False  # ถ้ารหัสผ่านไม่ถูกต้อง


# Function to fetch book details by ID
def fetch_book_from_db(book_id):
    with sqlite3.connect("book.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT book_id, book_name FROM books WHERE book_id = ?",
            (book_id,),
        )
        return cursor.fetchone()

# Function to update book details in the database
def update_book_in_db(book_id, book_name):
    with sqlite3.connect("book.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE books SET book_name = ? WHERE book_id = ?",
            (book_name, book_id),
        )
        conn.commit()

# ฟังก์ชันการเพิ่มหนังสือใหม่ไปที่ฐานข้อมูล book.db
def add_book_to_db(book_name):
    with sqlite3.connect("book.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO books (book_name) VALUES (?)", (book_name,))
        conn.commit()

# Route สำหรับหน้า Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        studentID = request.form["studentID"]
        password = request.form["password"]
        if verify_user(studentID, password):
            return redirect("/dashboard")
        else:
            flash("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง กรุณาลองใหม่", "danger")
    return render_template("login.html")

# Route สำหรับหน้า Signup
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        # Collect data from form
        prefix = request.form["prefix"]
        studentID = request.form["studentID"]
        firstName = request.form["firstName"]
        lastName = request.form["lastName"]
        year = request.form["year"]
        department = request.form["department"]
        accountNumber = request.form["accountNumber"]
        age = request.form["age"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]

        # Hash the password before saving to database
        hashed_password = hash_password(password)
        try:
            # Connect to the database and insert data
            print(prefix, studentID, firstName, lastName, year, department, accountNumber, age, email, phone, hashed_password)
            with sqlite3.connect("user.db") as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (prefix, studentID, firstName, lastName, year, department, accountNumber, age, email, phone, password) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (prefix, studentID, firstName, lastName, year, department, accountNumber, age, email, phone, hashed_password)
                )
                conn.commit()
            flash("สมัครสมาชิกสำเร็จ! กรุณาเข้าสู่ระบบ.", "success")
            return redirect("/login")
        except sqlite3.Error as e:
            print(f"An error occurred:\n {e}\n")
            if 'UNIQUE constraint failed: users.studentID' in str(e):
                flash("รหัสนักศึกษานี้มีผู้ใช้งานแล้ว", "danger")
            elif 'UNIQUE constraint failed: users.email' in str(e):
                flash("อีเมลนี้มีผู้ใช้งานแล้ว", "danger")
            else:
                flash("เกิดข้อผิดพลาดในการสมัครสมาชิก", "danger")

    return render_template("/login.html")

@app.route("/search_book", methods=["GET"])
def search_book():
    query = request.args.get("query", "")  # รับคำค้นหาจากฟอร์ม
    books = []  # เก็บผลลัพธ์การค้นหา
    if query:
        with sqlite3.connect("book.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT book_id, book_name
                FROM books
                WHERE book_name LIKE ?
                """,
                (f"%{query}%",),
            )
            books = cursor.fetchall()  # ดึงข้อมูลทั้งหมดที่ตรงกับคำค้นหา
            print(books)
    return render_template("search_book.html", books=books, query=query)

@app.route("/search_student", methods=["GET"])
def search_student():
    query = request.args.get("query", "")  # รับคำค้นหาจากฟอร์ม
    students = []  # เก็บผลลัพธ์การค้นหา
    if query:
        with sqlite3.connect("user.db") as conn:  # ใช้ฐานข้อมูล student.db
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, prefix, studentID, firstName, lastName, year, department, accountNumber, age, email, phone
                FROM users
                WHERE id LIKE ? OR prefix LIKE ? OR studentID LIKE ? OR firstName LIKE ? OR lastName LIKE ? OR department LIKE ? OR email LIKE ?
                """,
                (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%")
            )
            students = cursor.fetchall()  # ดึงข้อมูลทั้งหมดที่ตรงกับคำค้นหา
            print(students)  # พิมพ์ข้อมูลผลลัพธ์ใน Console

    return render_template("search_student.html", students=students, query=query)


@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        book_name = request.form["book_name"]
        try:
            # เพิ่มหนังสือใหม่ไปที่ฐานข้อมูล book.db
            add_book_to_db(book_name)
            flash("เพิ่มหนังสือสำเร็จ!", "success")
        except sqlite3.Error as e:
            flash(f"เกิดข้อผิดพลาด: {e}", "danger")

    return render_template("search_book.html")

@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    try:
        with sqlite3.connect("book.db") as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM books WHERE book_id = ?", (book_id,))
            conn.commit()
        flash("ลบหนังสือสำเร็จ!", "success")
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    if request.method == 'GET':
        # ดึงข้อมูลหนังสือจากฐานข้อมูล
        book = fetch_book_from_db(book_id)
        if book:
            return render_template('edit_book.html', book=book)
        else:
            flash("ไม่พบข้อมูลหนังสือที่ต้องการแก้ไข", "danger")
            return redirect(url_for('search_book'))

    if request.method == 'POST':
        # รับข้อมูลที่ถูกแก้ไขจากฟอร์ม
        book_name = request.form['book_name']
        # อัพเดตข้อมูลหนังสือในฐานข้อมูล
        update_book_in_db(book_id, book_name)
        flash("บันทึกการเปลี่ยนแปลงเรียบร้อยแล้ว!", "success")
        return redirect(url_for('search_book'))

# Route สำหรับหน้า Dashboard
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/search_book")
def book():
    return render_template("search_book.html")



# ฟังก์ชันในการรันแอปพลิเคชัน
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
