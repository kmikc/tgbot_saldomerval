import peewee
database = peewee.SqliteDatabase("saldomerval.db")

class saldomerval(peewee.Model):
    uniqid = peewee.CharField()
    chatid = peewee.CharField()
    cardnumber = peewee.CharField()
    username = peewee.CharField()
    id = peewee.CharField(primary_key=True)

    class Meta:
        database = database
