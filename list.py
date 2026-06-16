import gazu

gazu.set_host("http://localhost/api")
gazu.log_in("admin@example.com", "mysecretpassword")

print(gazu.client.get("data/projects/22d9ba26-2209-4910-bbaf-8528e4e8a5e0/budgets/bcebc78b-edaa-498d-ada8-2492eab78044/entries"))