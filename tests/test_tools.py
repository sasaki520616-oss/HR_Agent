import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.read_ops import (
    get_employee_info,
    get_employee_contact,
    get_employee_age,
    get_department_stats,
    calculate,
    get_current_date
)

test_cases = [
    {
        "name": "测试时间获取",
        "func": get_current_date.invoke,
        "args": {},
        "assert": lambda res: res is not None,
        "desc": "返回当前日期"
    },
    {
        "name": "查人-存在",
        "func": get_employee_info.invoke,
        "args": {"name": "陈建国"},
        "assert": lambda res: "employee_name" in res and "error" not in res,
        "desc": "能查到陈建国且返回了具体信息"
    },
    {
        "name": "查人-不存在(防崩)",
        "func": get_employee_info.invoke,
        "args": {"name": "张三丰"},
        "assert": lambda res: "error" in res,
        "desc": "查不存在的人应返回 error 字典，不能崩溃"
    },
    {
        "name": "查联系方式",
        "func": get_employee_contact.invoke,
        "args": {"name": "宋杰"},
        "assert": lambda res: "phone" in res and "email" in res,
        "desc": "查宋杰的联系方式并返回电话和邮箱"
    },
    {
        "name": "查年龄工龄",
        "func": get_employee_age.invoke,
        "args": {"name": "张丽"},
        "assert": lambda res: "age" in res and "tenure_years" in res,
        "desc": "查张丽的年龄和工龄"
    },

    {
        "name": "部门聚合统计",
        "func": get_department_stats.invoke,
        "args": {"dept_name": "前端研发组", "stat_type": "count"},
        "assert": lambda res: "result" in res,
        "desc": "SQL 原生聚合不报错"
    },
    {
        "name": "AST计算器-正常",
        "func": calculate.invoke,
        "args": {"expression": "100 * (3 + 2)"},
        "assert": lambda res: "500" in res,
        "desc": "精准算出 500"
    },
    {
        "name": "AST计算器-防攻击",
        "func": calculate.invoke,
        "args": {"expression": "2 ** 999999"},
        "assert": lambda res: "失败" in res,
        "desc": "指数爆炸被安全拦截"
    }
]

def run_tests():
    passed = 0
    total = len(test_cases)

    for case in test_cases:
        name = case["name"]
        try:
            result = case["func"](case["args"])
            if case["assert"](result):
                print(f"[PASS] {name} - {case['desc']}")
                print(f" {result}")
                passed += 1
            else:
                print(f"[FAIL] {name} - 期望: {case['desc']}")
                print(f"   [实际返回]: {result}")
        except Exception as e:
            print(f"[ERROR] {name} - 运行崩溃: {str(e)}")

        rate = (passed / total) *100
    print("=" * 50)
    print(f"Tool 测试汇总: 通过率 {passed}/{total} ({rate:.1f}%)")
    print("=" * 50)

if __name__ == "__main__":
    run_tests()

