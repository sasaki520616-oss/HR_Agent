import json
import time
import mysql.connector
from config import WORKER_DB_CONFIG


def get_connection():
    return mysql.connector.connect(**WORKER_DB_CONFIG, use_pure=True)


def review_requests():
    # 启动时先让 HR 选择要处理的池子
    print("【HR 审批端】已启动。")
    print("1. 审批新工单 (PENDING)")
    print("2. 处理挂起工单 (HOLD)")
    pool_choice = input("请选择要处理的工单池 (1/2): ")

    if pool_choice == '2':
        target_status = 'HOLD'
    else:
        target_status = 'PENDING'

    print(f"正在监听 [{target_status}] 工单...")

    while True:
        time.sleep(5)
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        try:
            # 动态查 PENDING 或 HOLD
            cur.execute(f"SELECT * FROM change_requests WHERE status = %s ORDER BY id ASC LIMIT 10", (target_status,))
            reqs = cur.fetchall()

            if not reqs:
                # 如果是挂起池，查空了就退出去重新选（或者继续等）
                if target_status == 'HOLD':
                    print("\n当前没有挂起的工单了。")
                    break  # 退出循环，回到最开始重新选
                continue

            for req in reqs:
                payload = json.loads(req["payload"]) if isinstance(req["payload"], str) else req["payload"]
                old_data = json.loads(req['old_data']) if isinstance(req['old_data'], str) else req['old_data']

                print(f"\n================ [HR 审批台 - {target_status}] ================")
                print(f"单号: {req['id']} | 动作: {req['action']}")
                print(f"申请理由: {req['reason']}")
                print(f"【修改前快照】: {json.dumps(old_data, ensure_ascii=False)}")
                print(f"【申请修改为】: {json.dumps(payload, ensure_ascii=False)}")

                decision = input("(y)批准 / (n)拒绝 / (p)跳过并挂起: ")

                if decision.lower() == 'y':
                    cur.execute(
                        "UPDATE change_requests SET status = 'APPROVED', approved_by = 'HR_Admin' WHERE id = %s",
                        (req['id'],))
                    print(f">>> 工单 {req['id']} 已批准，等待后台执行。")
                elif decision.lower() == 'n':
                    cur.execute(
                        "UPDATE change_requests SET status = 'REJECTED', approved_by = 'HR_Admin' WHERE id = %s",
                        (req['id'],))
                    print(f">>> 工单 {req['id']} 已拒绝。")
                elif decision.lower() == 'p':
                    # 如果是在挂起池里继续按 p，就保持 HOLD；如果是在 PENDING 里按 p，就变成 HOLD
                    cur.execute("UPDATE change_requests SET status = 'HOLD' WHERE id = %s", (req['id'],))
                    print(f">>> 工单 {req['id']} 已挂起。")
                    continue

            conn.commit()

        except Exception as e:
            print(f"审批端异常: {e}")

        finally:
            cur.close()
            conn.close()


if __name__ == "__main__":
    review_requests()