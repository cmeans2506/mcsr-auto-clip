import portalocker
import sys

lock_file = "mcsr_auto_clip.lock"
try:
    fp = open(lock_file, "w")
    portalocker.lock(fp, portalocker.LOCK_EX | portalocker.LOCK_NB)
except portalocker.exceptions.LockException:
    print("重复运行脚本，退出")
    sys.exit()


from auto_clip import auto_clip

if __name__ == "__main__":
    auto_clip.run()