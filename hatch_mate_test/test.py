# data ={"source_rack":"123","target_rack":"123","rack":"43","tube":"32",
# "source_not_move":"1,5,44-55","target_not_move":"23-66","source_move":"20","target_move":"1-5","tube_num":"5"}
# import random
# source_area = data['source_move'].split(',')
# source_no = []
# for i in source_area:
#     try:
#         i.split('-')
#         for y in range(int(i.split('-')[0]),int(i.split('-')[1])+1):
#             source_no.append(y)
#     except:
#         source_no.append(int(i))
# print(random.choice(source_no))
# print(random.randint(1000,100000000000))
# a = []
# if a:
#     print(1)
# else:
#     print(2)
class a:
    global ss
    ss= 123
    def b(self):
        ss = 1
        print(ss)
    def c(self):
        global ss
        print(ss)
        ss = 2
        print(ss)
    def d(self):
        print(ss)

h= a()
h.ss = 123
print(h.ss)
# h.c()
# h.d()
A= a()
print(A.ss)
A.ss =1232
print(A.ss)
# A.d()
