import hashlib


def sha1(file_path) -> str:
    sha1_func = hashlib.sha1()
    try:
        a = open(fr'{file_path}', 'rb')
    except:
        print('文件路径有误，请输入正确路径！')
        return ""
    while True:
        b = a.read(4096)  # 这里就是每次读文件放进内存的大小，小心溢出！
        sha1_func.update(b)
        if not b:
            break
    a.close()
    result = sha1_func.hexdigest()
    return result
