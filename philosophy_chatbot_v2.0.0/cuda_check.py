import torch
print(torch.cuda.is_available())
# Kết quả phải là True
print(torch.cuda.get_device_name(0))
# Sẽ in ra tên GPU của bạn