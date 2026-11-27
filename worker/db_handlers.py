def handle_offboard(cur, payload):
    """处理离职申请"""
    cur.execute("UPDATE employees SET status = 'inactive' WHERE employee_no = %s",
                (payload['employee_no'],))

def handle_update_phone(cur, payload):
    """处理联系方式修改"""
    if 'phone' in payload:
        cur.execute("UPDATE employees SET phone = %s WHERE employee_no = %s",
                    (payload['phone'], payload['employee_no']))
    if 'email' in payload:
        cur.execute("UPDATE employees SET email = %s WHERE employee_no = %s",
                    (payload['email'], payload['employee_no']))


action_handlers = {
    "offboard": handle_offboard,
    "update_phone": handle_update_phone
}