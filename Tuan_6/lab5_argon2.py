import hashlib
import time

from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError

pwd = "example-password"

print("SHA-256 lần 1:", hashlib.sha256(pwd.encode()).hexdigest())
print("SHA-256 lần 2:", hashlib.sha256(pwd.encode()).hexdigest())
print()

ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, type=Type.ID)

start = time.perf_counter()
stored1 = ph.hash(pwd)
elapsed = time.perf_counter() - start
stored2 = ph.hash(pwd)

print("Argon2id lần 1:", stored1)
print("Argon2id lần 2:", stored2)
print(f"Thời gian hash: {elapsed * 1000:.0f} ms")
print()

try:
    ph.verify(stored1, pwd)
    print("verify đúng mật khẩu: OK")
except VerifyMismatchError:
    print("verify đúng mật khẩu: FAIL")

try:
    ph.verify(stored1, "wrong-password")
    print("verify sai mật khẩu: OK")
except VerifyMismatchError:
    print("verify sai mật khẩu: VerifyMismatchError")

print("check_needs_rehash:", ph.check_needs_rehash(stored1))
weak = PasswordHasher(time_cost=1, memory_cost=8, parallelism=1, type=Type.ID).hash(pwd)
print("check_needs_rehash (hash tham số yếu):", ph.check_needs_rehash(weak))