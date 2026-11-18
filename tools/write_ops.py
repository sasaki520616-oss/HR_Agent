import mysql.connector
import json
import hashlib
from langchain_core.tools import tool
from tools.utils import get_connection, handle_multiple_matches


def submit_change_request(action: str, payload: dict, reason: str = None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        payload_str = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        idem_key = hashlib.sha256(f"{action}|{payload_str}".encode()).hexdigest()

        cur.execute("""
            INSERT INTO change_requests (action, payload, requested_by, reason, idempotency_key)
            VALUES (%s, %s, %s, %s, %s)
        """, (action, payload_str, "agent", reason, idem_key))
        conn.commit()

        return {
            "status": "success",
            "message": f"已成功创建待审批工单，单号 {cur.lastrowid}。等待管理员处理。",
        }
    except mysql.connector.IntegrityError:
        return {"error": "该申请已存在（重复提交），请勿重复操作。"}
    except Exception as e:
        return {"error": f"工单创建失败: {str(e)}"}
    finally:
        cur.close()
        conn.close()


# ============ 写操作工具 ===================
@tool
@handle_multiple_matches
def request_offboard(name: str = None, employee_no: str = None, reason: str = None):
    """提交员工离职申请。调用此工具只会生成待审批工单，不会直接删除数据。"""
    payload = {"employee_no": employee_no}
    return submit_change_request("OFFBOARD", payload, reason=reason)


@tool
@handle_multiple_matches
def request_update_info(name: str = None, employee_no: str = None, new_phone: str = None, reason: str = None):
    """提交修改员工联系方式申请。"""
    payload = {"employee_no": employee_no, "new_phone": new_phone}
    return submit_change_request("UPDATE_INFO", payload, reason=reason)

write_tools = [
    request_offboard,
    request_update_info
]