import psycopg2
mydb = psycopg2.connect(user='kdjmispwzuqrpa', password='79fabf4112ead809504789c52d5037b2ecdd9967a4a4ef9c64c79df78bf36064', host='ec2-54-74-14-109.eu-west-1.compute.amazonaws.com', database='d8lued2265pr44')
db = mydb.cursor()
db.execute("SELECT * FROM cards")
rows = db.fetchall()
print(rows)