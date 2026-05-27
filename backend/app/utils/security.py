"""
哈希和验证密码的工具函数
"""

from pwdlib import PasswordHash

pwd_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return pwd_hasher.hash(password)


def verify_password(password: str, hash: str) -> bool:
    return pwd_hasher.verify(password, hash)
