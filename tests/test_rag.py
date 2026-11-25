import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.policy_tool import search_policy

# 定义测试用例
test_cases = [
    {
        "name": "RAG-正常检索",
        "query": "迟到怎么扣钱？",
        "expect_fail": False,
        "desc": "应能检索到具体的考勤制度"
    },
    {
        "name": "RAG-正常检索",
        "query": "怎么请假？",
        "expect_fail": False,
        "desc": "应能检索到具体的考勤制度"
    },
    {
        "name": "RAG-防幻觉",
        "query": "公司给员工发火星飞船吗？",
        "expect_fail": True,
        "desc": "无关问题应返回未收录/未找到"
    },
    {
        "name": "RAG-防幻觉",
        "query": "薪资结构？",
        "expect_fail": True,
        "desc": "无关问题应返回未收录/未找到"
    }
]


def run_tests():
    passed = 0
    total = len(test_cases)

    for case in test_cases:
        name = case["name"]
        query = case["query"]

        try:
            # 调用 RAG 工具
            result = search_policy.invoke({"query": query})

            # 判断是否触发了兜底话术（简单粗暴地匹配关键字）
            is_miss = any(keyword in result for keyword in ["未收录", "未找到", "没有相关", "抱歉"])

            if case["expect_fail"]:
                # 期望是查不到的（防幻觉）
                if is_miss:
                    print(f"[PASS] {name} - 成功拦截无关问题")
                    passed += 1
                else:
                    print(f"[FAIL] {name} - 期望拦截，但检索到了内容")
                    print(f"   [检索返回]: {result}")
            else:
                # 期望是查得到的
                if not is_miss and len(result) > 10:
                    print(f"[PASS] {name} - 成功检索到制度")
                    passed += 1
                else:
                    print(f"[FAIL] {name} - 期望检索到内容，但返回了兜底或为空")
                    print(f"   [检索返回]: {result}")

        except Exception as e:
            print(f"[ERROR] {name} - 运行崩溃: {str(e)}")

    rate = (passed / total) * 100
    print("=" * 50)
    print(f"RAG 测试汇总: 通过率 {passed}/{total} ({rate:.1f}%)")
    print("=" * 50)

if __name__ == "__main__":
    run_tests()