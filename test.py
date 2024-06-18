with open('users.txt', 'r', encoding='utf-8') as file:
    # print(file.read())
    str_ = file.read()
    print(str_.split('\n'))
    user_id_list = [data[0] for data in file.read().split(',') if file.read()]
