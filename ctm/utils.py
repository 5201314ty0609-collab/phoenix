"""CTM 共享工具函数"""


def estimate_tokens(text: str) -> int:
    """粗略估算文本的 token 数（约 4 字符 = 1 token）"""
    return len(text) // 4
