from config import DB_CONFIG
import functools
import mysql.connector
import sys, os

# ============== 建数据库连接、查重名装饰器 ===============

def get_connection():
    return mysql.connector.connect(**DB_CONFIG, use_pure=True)

def handle_multiple_matches(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        name = kwargs.get("name")
        employee_no = kwargs.get("employee_no")

        if employee_no:
            return func(*args, **kwargs)
        if not name:
            return {"error": "必须提供员工姓名(name)或工号(employee_no)。"}

        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("""
                select e.id, e.employee_no, e.name, d.dept_name, p.title 
                from employees e
                left join departments d ON e.department_id = d.id
                left join positions p ON e.position_id = p.id
                where e.name = %s and e.status = 'active'
            """, (name,))
            records = cur.fetchall()
        finally:
            cur.close()
            conn.close()

        if not records:
            return {"error": f"未找到名为 '{name}' 的员工。"}
        if len(records) > 1:
            return {
                "status": "multiple_matches",
                "message": f"系统中有多个名为 '{name}' 的员工，请让用户提供工号或部门确认。",
                "candidates": records
            }

        kwargs['employee_no'] = records[0]['employee_no']
        return func(*args, **kwargs)
    return wrapper
