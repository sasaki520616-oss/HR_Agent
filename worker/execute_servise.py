import json
import time
import mysql.connector
from config import WORKER_DB_CONFIG

def get_connection():
    return mysql.connector.connect(**WORKER_DB_CONFIG, use_pure=True)

def process_requests():
    print("后台审批服务已启动，正在监听工单...")
    while True:
        time.sleep(5)

        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        try:
            cur.execute("SELECT * FROM change_requests WHERE status = 'PENDING' ORDER BY id ASC limit 1")
            req = cur.fetchone()

            if not req:
                print("当前没有待审批的工单。")
                continue

            print(f"\n================ [工单审批] ================")
            print(f"单号: {req['id']} | 动作: {req['action']}")
            print(f"申请理由: {req['reason']}")

            payload = json.loads(req['payload']) if isinstance(req['payload'], str) else req['payload']
            print(f"具体内容: {json.dumps(payload, ensure_ascii=False)}")

            decision = input("是否批准并执行？(y/n): ")

            if decision.lower() == 'y':
                try:
                    if req['action'] == "OFFBOARD":
                        print(f">>> 执行：将员工 {payload['employee_no']} 状态改为 inactive...")
                        cur.execute("UPDATE employees SET status = 'inactive' WHERE employee_no = %s",
                                    (payload['employee_no'],))

                    elif req['action'] == "UPDATE_INFO":
                        if payload.get('new_phone'):
                            print(f">>> 执行：更新员工 {payload['employee_no']} 电话为 {payload['new_phone']}...")
                            cur.execute("UPDATE employees SET phone = %s WHERE employee_no = %s",
                                        (payload['new_phone'], payload['employee_no']))

                    cur.execute("UPDATE change_requests SET status = 'EXECUTED', approved_by = 'admin' WHERE id = %s",
                                (req['id'],))
                    conn.commit()
                    print(f">>> 工单 {req['id']} 执行完毕。")

                except Exception as e:
                    conn.rollback()
                    cur.execute("UPDATE change_requests SET status = 'FAILED' WHERE id = %s", (req['id'],))
                    conn.commit()
                    print(f">>> 工单 {req['id']} 执行失败，已回滚: {str(e)}")
            else:
                cur.execute("UPDATE change_requests SET status = 'REJECTED', approved_by = 'admin' WHERE id = %s",
                            (req['id'],))
                conn.commit()
                print(f">>>工单 {req['id']} 已被拒绝。")

        except Exception as e:
            print(f"工单处理发生异常: {e}")

        finally:
            cur.close()
            conn.close()


if __name__ == "__main__":
    process_requests()
