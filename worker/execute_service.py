import json
import time
import mysql.connector
from config import WORKER_DB_CONFIG
from worker.db_handlers import action_handlers

def get_connection():
    return mysql.connector.connect(**WORKER_DB_CONFIG, use_pure=True)

def execute_requests():
    print("【后台执行器】已启动，正在轮询 APPROVED 工单...")
    while True:
        time.sleep(5)
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        try:
            cur.execute("SELECT * FROM change_requests WHERE status = 'APPROVED' ORDER BY id ASC LIMIT 1")
            req = cur.fetchone()

            if not req:
                continue

            # 抢锁
            cur.execute("UPDATE change_requests SET status = 'EXECUTING' WHERE id = %s AND status = 'APPROVED'", (req['id'],))
            if cur.rowcount == 0:
                conn.rollback()
                continue
            conn.commit()

            print(f"\n>>> [执行器] 抢到工单 {req['id']}，开始执行...")
            payload = json.loads(req['payload']) if isinstance(req['payload'], str) else req['payload']

            try:
                handler = action_handlers.get(str(req['action']))
                if not handler:
                    raise ValueError(f"未知的工单动作: {req['action']}")

                handler(cur, payload)

                if cur.rowcount == 0:
                    raise ValueError("执行失败：目标记录不存在，或数据没有发生实际变化。")

                cur.execute("UPDATE change_requests SET status = 'EXECUTED' WHERE id = %s", (req['id'],))
                conn.commit()
                print(f">>> 工单 {req['id']} 执行成功！")

            except Exception as e:
                conn.rollback()
                cur.execute("UPDATE change_requests SET status = 'FAILED' WHERE id = %s", (req['id'],))
                conn.commit()
                print(f">>> 工单 {req['id']} 执行失败: {str(e)}")

        except Exception as e:
            print(f"执行器发生异常: {e}")
        finally:
            cur.close()
            conn.close()

if __name__ == "__main__":
    execute_requests()