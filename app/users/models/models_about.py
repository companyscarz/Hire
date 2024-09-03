import sqlite3
from sqlite3 import Error
from datetime import datetime, timedelta
from flask import flash 

current_time = datetime.utcnow()

#about database
class ABout():
    def __init__(self, suggestion, created_at):
        self.suggestion = suggestion
        self.created_at = created_at
        
    def add(self):
        try:
            conn = sqlite3.connect('hire.db')
            cur = conn.cursor()
            cur.execute(""" CREATE TABLE if not exists Aboutdb (
	                               Id INTEGER PRIMARY KEY AUTOINCREMENT,
	                               Suggestion TEXT, 
	                               Created_at DATETIME
	                               )""")
	                               
            data = [self.suggestion, self.created_at]
            cur.execute(""" 
	                                INSERT INTO Aboutdb(Suggestion, created_at) VALUES(?,?)
	            """, data)
            conn.commit()
            conn.close()
        except Error as e:
	        flash(f"⚠An Error occured: {e}")  
        
    
    
    def drop(self):
        try:
            conn = sqlite3.connect('hire.db')
            cur = conn.cursor()
            cur.execute(''' DROP TABLE Aboutdb ''')
            conn.commit()
            conn.close()
        except Error as e:
	        flash(f"⚠An Error occured: {e}")  
    
    def show(self):
        try:
            conn = sqlite3.connect('hire.db')
            cur = conn.cursor()
            cur.execute(""" CREATE TABLE if not exists Aboutdb (
	                               Id INTEGER PRIMARY KEY AUTOINCREMENT,
	                               Suggestion TEXT, 
	                               Created_at DATETIME
	                               )""")
			
	        #check for objects older than 3 weeks
            three_weeks_ago = current_time - timedelta(weeks=3)
	        
	        #only show data that is less than 3 weekes old
            info = conn.execute(""" 
	                                    SELECT Id, Suggestion, Created_at  FROM Aboutdb WHERE Created_at > ? ORDER BY Id DESC
	                                    """,(three_weeks_ago,))
            return info    #return access to the values
            conn.commit()
            conn.close()
        except Error as e:
	        flash(f"⚠An Error occured: {e}")  
