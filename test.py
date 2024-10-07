from client_functions import *

config = load_config()

conn = connect(config)

data, data2 = get_data_struct(conn)
json1 = gen_json(data, data2, conn)
json1 = filter_data(json1,["programming","mechanical"])
print(json1)

