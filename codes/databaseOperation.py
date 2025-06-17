from dotenv import load_dotenv

import mysql.connector
import os

class DatabaseOperation:

    def __init__(self):

        load_dotenv(dotenv_path=".env")
        self.host = os.getenv('MYSQL_HOST')
        self.user = os.getenv('MYSQL_USERNAME')
        self.password = os.getenv('MYSQL_PASSWORD')
        self.database = os.getenv('MYSQL_DB')

        #print(f"{self.host}{self.user}{self.password}{self.database}")

        try:
            self.mydb = mysql.connector.connect(host=self.host, user=self.user, password=self.password, database=self.database)
            self.mycursor = self.mydb.cursor()
        except:
            print("Database Connection Error ... ")

    def dbSelect(self, sql):
        self.mycursor.execute(sql)
        myresult = self.mycursor.fetchall()
        return myresult, self.mycursor.rowcount

    def dbSelectOnly(self, sql):
        rtn = ""
        self.mycursor.execute(sql)
        myresult = self.mycursor.fetchone()
        for row in myresult:
            rtn = row
        return rtn

    def dbInsert(self, sql):
        self.mycursor.execute(sql)
        self.mydb.commit()

    def dbDelete(self, sql):
        self.mycursor.execute(sql)
        self.mydb.commit()

    def dbUpdate(self, sql):
        self.mycursor.execute(sql)
        self.mydb.commit()

    def dbCommit(self):
        self.mydb.commit()

    def dbClose(self):
        self.mydb.close()
