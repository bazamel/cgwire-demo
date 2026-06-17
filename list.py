import gazu

gazu.set_host("http://localhost/api")
gazu.log_in("admin@example.com", "mysecretpassword")

person = gazu.person.all_persons()[0]
print(gazu.person.get_person(person["id"], relations = True))