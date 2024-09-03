import sqlite3
from sqlite3 import Error
from datetime import datetime, timedelta
from flask import flash 
current_time = datetime.utcnow()

#block database
class BLock():
    def __init__(self, email, created_at):
        self.email = email
        self.created_at = created_at
        
    def add(self):
        try:
            conn = sqlite3.connect('hire.db')
            cur = conn.cursor()
            cur.execute(""" CREATE TABLE if not exists Blockdb (
	                               Id INTEGER PRIMARY KEY AUTOINCREMENT,
	                               Email TEXT, 
	                               Created_at DATETIME
	                               )""")
	                               
            data = [self.email, self.created_at]
            cur.execute(""" 
	                                INSERT INTO Blockdb(Email, created_at) VALUES(?,?)
	            """, data)
            conn.commit()
            conn.close()
        except Error as e:
	        flash(f"⚠An Error occured: {e}")  
    
    def drop(self):
        try:
            conn = sqlite3.connect('hire.db')
            cur = conn.cursor()
            cur.execute(''' DROP TABLE Blockdb ''')
            conn.commit()
            conn.close()
        except Error as e:
	        flash(f"⚠An Error occured: {e}")  
    
    def show(self):##this shows descending data in the admin pages
        try:
            conn = sqlite3.connect('hire.db')
            cur = conn.cursor()
            cur.execute(""" CREATE TABLE if not exists Blockdb (
	                               Id INTEGER PRIMARY KEY AUTOINCREMENT,
	                               Email TEXT, 
	                               Created_at DATETIME
	                               )""")
			
	        #check for objects older than 3 weeks
            #three_weeks_ago = current_time - timedelta(weeks=3)
	        
	        #only show data that is less than 3 weekes old
            info = conn.execute(""" 
	                                    SELECT Id, Email  FROM Blockdb ORDER BY Id DESC """)
            return info    #return access to the values
            conn.commit()
            conn.close()
        except Error as e:
            flash(f"⚠An Error occured: {e}")  
              
     #Delete row   
    def delete_row_from_database(self, row_id):
        try:
            conn = sqlite3.connect('hire.db')
            cur = conn.cursor()   
            cur.execute(""" 
	                                DELETE FROM Blockdb WHERE ID = ? 
	                                    """,(row_id))
            flash("Data deleted successfully!!")
            conn.commit()
            conn.close()
        except Error as e:
	        flash(f"⚠An Error occured: {e}")
	        
	        
##check is email is blocked
    def is_email_blocked(self, email):
    	try:
    		conn = sqlite3.connect('hire.db')
    		cur = conn.cursor()
    		cur.execute(""" CREATE TABLE if not exists Blockdb (
	                               Id INTEGER PRIMARY KEY AUTOINCREMENT,
	                               Email TEXT, 
	                               Created_at DATETIME
	                               )""")
    		cur.execute(''' SELECT COUNT(*) from Blockdb WHERE Email = ?''',(email,))
    		result = cur.fetchone()
    		return result[0] >0
    	except Error as e:
    		flash(f"⚠An Error occured: {e}")