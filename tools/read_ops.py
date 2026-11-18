import mysql.connector
from datetime import date
import ast
import operator
from langchain_core.tools import tool
from tools.utils import get_connection, handle_multiple_matches


# ============ 基础信息查询工具 ===================
@tool
def get_current_date():
    """获取当前系统日期时间，格式：YYYY-MM-DD。用于相对时间推算。"""
    return str(date.today())


@tool
@handle_multiple_matches
def get_employee_info(name: str = None, employee_no: str = None):
    """员工基本信息查询工具，用于查询员工的部门、岗位、上级名字（直系领导）。"""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
        select e.name as employee_name, d.dept_name, p.title, m.name as manager_name
        from employees e
        left join departments d on e.department_id = d.id
        left join positions p on e.position_id = p.id
        left join employees m on e.manager_id = m.id
        where e.employee_no = %s and e.status = 'active'
        """, (employee_no,))
        rec = cur.fetchone()

        if rec is None:
            return {"error": f"未找到该员工，请重新确认其姓名或工号。"}
        if rec.get('manager_name') is None:
            rec['manager_name'] = '无'
        if rec.get('title') is None:
            rec['title'] = '无'
        return rec

    finally:
        cur.close()
        conn.close()


@tool
@handle_multiple_matches
def get_employee_contact(name: str = None, employee_no: str = None):
    """员工联系方式查询工具，用于查询某位员工的电话和邮箱"""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
        select e.name as employee_name, e.phone, e.email
        from employees e
        where e.employee_no = %s and e.status = 'active'
        """, (employee_no,))
        rec = cur.fetchone()
        if rec is None:
            return {"error": f"未找到该员工的通讯方式，请重新确认其姓名或工号。"}
        return rec

    finally:
        cur.close()
        conn.close()


@tool
@handle_multiple_matches
def get_employee_age(name: str = None, employee_no: str = None):
    """员工年龄工龄查询工具，用于查询某员工的年龄和工龄。"""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
        select e.name as employee_name, e.birth_date, e.hire_date,
            TIMESTAMPDIFF(YEAR, e.birth_date, CURDATE()) as age,
            TIMESTAMPDIFF(YEAR, e.hire_date, CURDATE()) as tenure_years
        from employees e
        where e.employee_no = %s and e.status = 'active'
        """, (employee_no,))
        rec = cur.fetchone()

        if rec is None:
            return {"error": f"未找到工号为 {employee_no} 的员工数据。"}
        if rec["age"] is None:
            return {"name": rec["employee_name"], "hire_date": rec["hire_date"],
                    "error": "该员工出生日期缺失，无法计算年龄。"}
        if rec["tenure_years"] is None:
            return {"name": rec["employee_name"], "birth_date": rec["birth_date"],
                    "error": "该员工入职时间缺失，无法计算工龄。"}

        return {"name": rec["employee_name"], "age": rec["age"], "tenure_years": rec["tenure_years"]}
    finally:
        cur.close()
        conn.close()


@tool
def get_department_members(dept_name: str):
    """查询部门成员名单。最多返回 20 人；超过 20 人返回 partial_success 并提示截断。"""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
        select e.name
        from employees e
        join departments d on e.department_id = d.id
        where d.dept_name = %s and e.status = 'active'
        limit 21
        """, (dept_name,))
        recs = cur.fetchall()

        if not recs:
            return {"error": f"未找到部门 '{dept_name}' 或该部门无在职员工。"}

        if len(recs) == 21:
            return {
                "status": "partial_success",
                "message": "数据量较大，这里仅展示前20名员工名单。",
                "data": recs[:20]
            }
        return {"status": "success", "data": recs}
    finally:
        cur.close()
        conn.close()


# ===============考勤类工具 ================
@tool
@handle_multiple_matches
def get_employee_attendance(work_date: str, name: str = None, employee_no: str = None):
    """员工考勤工具，用于查询员工某天的考勤情况。"""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute("""
        select e.name, a.check_in_time, a.check_out_time, a.status, a.late_minutes, a.early_leave_minutes
        from attendance a
        join employees e on a.employee_id = e.id
        where a.work_date = %s and e.employee_no = %s and e.status = 'active'
        limit 20
        """, (work_date, employee_no))
        rec = cur.fetchone()
        if rec is None:
            return {"error": f"未找到该员工{work_date} 的考勤信息，请核对姓名或日期。"}
        return rec

    finally:
        cur.close()
        conn.close()


@tool
@handle_multiple_matches
def get_employee_attendance_history(month_state: str, name: str = None, employee_no: str = None):
    """员工月考勤统计工具，用于记录员工一个月的考勤情况（迟到次数、缺勤天数等）。"""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute("""
        select e.name, a.normal_days, a.late_count, a.early_leave_count, a.absent_days, a.leave_days
        from attendance_history a
        join employees e on a.employee_id = e.id
        where a.month_state = %s and e.employee_no = %s and e.status = 'active'
        limit 20
        """, (month_state, employee_no))
        rec = cur.fetchone()
        if rec is None:
            return {"error": f"未找到该员工{month_state} 的考勤汇总信息，请核对姓名或月份。"}
        return rec

    finally:
        cur.close()
        conn.close()


# =========== 统计分析类工具 ===============
@tool
def get_department_stats(dept_name: str, stat_type: str) -> dict:
    """
    部门数据统计工具。用于获取某个部门的聚合统计数据。
    【参数说明】
    - dept_name: 部门名称，例如 "研发部"。
    - stat_type: 统计类型。只能传入以下英文枚举值之一：
      - "count": 统计部门总人数。空部门返回 0。
      - "avg_age": 统计部门平均年龄。空部门返回 error。
      - "max_age": 统计部门最大年龄。空部门返回 error。
      - "min_age": 统计部门最小年龄。空部门返回 error。
      - "avg_tenure": 统计部门平均工龄（年）。空部门返回 error。
      - "gender_count": 统计部门男女人数分布。
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        base_join = """
            FROM employees e
            JOIN departments d ON e.department_id = d.id
            WHERE d.dept_name = %s AND e.status = 'active'
        """

        if stat_type == "gender_count":
            cur.execute(f"""
                SELECT e.gender, COUNT(e.id) as count
                {base_join}
                GROUP BY e.gender
            """, (dept_name,))
            recs = cur.fetchall()
            if not recs:
                return {"error": f"未找到部门 '{dept_name}' 的有效数据。"}

            gender_stats = {"男": 0, "女": 0}
            unknown = []
            for r in recs:
                g = str(r.get("gender", "")).strip().upper()
                if g == "M":
                    gender_stats["男"] += r.get("count", 0)
                elif g == "F":
                    gender_stats["女"] += r.get("count", 0)
                else:
                    unknown.append({"gender": r.get("gender"), "count": r.get("count", 0)})

            total = gender_stats["男"] + gender_stats["女"] + sum(u["count"] for u in unknown)
            result = {
                "dept_name": dept_name,
                "stat_type": "gender_count",
                "data": gender_stats,
                "total": total,
                "message": f"{dept_name}性别分布：男 {gender_stats['男']} 人，女 {gender_stats['女']} 人，共 {total} 人",
            }
            if unknown:
                result["data_quality_warning"] = {
                    "message": "检测到不符合 M/F 契约的 gender 值，请检查数据源",
                    "rows": unknown,
                }
            return result

        stat_sql = {
            "count": "SELECT COUNT(e.id) as result, '人' as unit {base}",
            "avg_age": "SELECT ROUND(AVG(TIMESTAMPDIFF(YEAR, e.birth_date, CURDATE())), 1) as result, '岁' as unit {base}",
            "max_age": "SELECT MAX(TIMESTAMPDIFF(YEAR, e.birth_date, CURDATE())) as result, '岁' as unit {base}",
            "min_age": "SELECT MIN(TIMESTAMPDIFF(YEAR, e.birth_date, CURDATE())) as result, '岁' as unit {base}",
            "avg_tenure": "SELECT ROUND(AVG(TIMESTAMPDIFF(YEAR, e.hire_date, CURDATE())), 1) as result, '年' as unit {base}"
        }

        if stat_type not in stat_sql:
            return {"error": "不支持的统计类型，请检查 stat_type 参数。"}

        sql = stat_sql[stat_type].format(base=base_join)
        cur.execute(sql, (dept_name,))
        rec = cur.fetchone()

        if stat_type == "count":
            n = rec["result"] if rec else 0
            return {"dept_name": dept_name, "stat_type": "count",
                    "result": n, "unit": "人",
                    "message": f"{dept_name}共 {n} 人" + ("（部门无在职员工）" if n == 0 else "")}

        if rec is None or rec['result'] is None:
            return {"error": f"未找到部门 '{dept_name}' 的有效统计数据（可能无人或日期缺失）。"}

        return {
            "dept_name": dept_name,
            "stat_type": stat_type,
            "result": rec['result'],
            "unit": rec['unit'],
            "message": f"{dept_name}的统计结果为 {rec['result']} {rec['unit']}"
        }

    finally:
        cur.close()
        conn.close()


# =========== 计算器工具 ===============
ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}

MAX_EXPR_LEN = 200
MAX_POW_EXP = 100


def _safe_eval(node):
    if isinstance(node, ast.Constant):
        if not isinstance(node.value, (int, float)):
            raise TypeError("仅支持数字常量")
        return node.value
    if isinstance(node, ast.BinOp):
        if type(node.op) not in ALLOWED_OPERATORS:
            raise TypeError(f"不支持的运算符: {type(node.op).__name__}")
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > MAX_POW_EXP:
            raise ValueError(f"指数绝对值超过上限 {MAX_POW_EXP}")
        return ALLOWED_OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp):
        if type(node.op) not in ALLOWED_OPERATORS:
            raise TypeError(f"不支持的一元运算符: {type(node.op).__name__}")
        return ALLOWED_OPERATORS[type(node.op)](_safe_eval(node.operand))
    raise TypeError(f"不支持的数学运算: {type(node).__name__}")


@tool
def calculate(expression: str) -> str:
    """数学计算器，用于执行基础算术运算（加减乘除、括号、幂）。
    仅作为兜底：年龄/工龄等聚合优先调用 get_department_stats。
    禁止用本工具对部门明细做批量聚合。"""
    if len(expression) > MAX_EXPR_LEN:
        return f"计算失败：表达式长度超过 {MAX_EXPR_LEN} 字符上限。"
    try:
        node = ast.parse(expression, mode='eval').body
        result = _safe_eval(node)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return f"计算结果为: {result}"
    except Exception as e:
        return f"计算失败，请检查算式是否正确。错误信息: {str(e)}"


# 工具注册列表
db_tools = [
    get_current_date,
    get_employee_info,
    get_employee_contact,
    get_employee_age,
    get_department_members,
    get_employee_attendance,
    get_employee_attendance_history,
    get_department_stats,
    calculate
]