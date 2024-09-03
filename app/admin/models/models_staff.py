import sqlite3
from sqlite3 import Error
from datetime import datetime, timedelta
from flask import flash 

current_time = datetime.utcnow()

class STaff():
    def __init__(self, name, email, telphone, file_data, filename, content_type, gender, password, created_at):
        self.name = name 
        self.email = email
        self.telphone =telphone
        self.file_data = file_data
        self.filename = filename 
        self.content_type = content_type
        self.gender = gender
        self.password = password
        self.created_at = created_at
        
    def add(self):
        try:
	        conn = sqlite3.connect('hire_admin.db')
	        cur = conn.cursor()
	        cur.execute(""" CREATE TABLE if not exists Staff_db (
	                               Id INTEGER PRIMARY KEY AUTOINCREMENT,
	                               Name TEXT,
	                               Email TEXT,
                                   Telphone TEXT,
	                               File_data TEXT,
	                               Filename TEXT,
	                               Content_type TEXT,
	                               Gender TEXT,
	                               Password TEXT,
	                               Created_at DATETIME
	                               )""")
	                               
	        data = [self.name, self.email, self.telphone,  self.file_data, self.filename, self.content_type, self.gender, self.password, self.created_at]
	        cur.execute(""" 
	                                INSERT INTO Staff_db(Name, Email, Telphone, File_data, Filename, Content_type, Gender, Password, Created_at) VALUES(?,?,?,?,?,?,?,?,?)
	            """, data)
	        conn.commit()
	        conn.close()
        except Error as e:
	        conn.commit()
	        conn.close()
	        flash(f"An Error occured⚠: {e}")
    
    def drop(self):
        try:
	        conn = sqlite3.connect('hire_admin.db')
	        cur = conn.cursor()
	        cur.execute(''' DROP TABLE Staff_db ''')
	        conn.commit()
	        conn.close()
        except Error as e:
	        conn.commit()
	        conn.close()
	        flash(f"An Error occured⚠: {e}")  
    
    def show(self):
        try:
	        conn = sqlite3.connect('hire_admin.db')
	        cur = conn.cursor()
	        cur.execute(""" CREATE TABLE if not exists Staff_db (
	                               Id INTEGER PRIMARY KEY AUTOINCREMENT,
	                               Name TEXT,
	                               Email TEXT,
                                   Telphone TEXT,
	                               File_data TEXT,
	                               Filename TEXT,
	                               Content_type TEXT,
	                               Gender TEXT,
	                               Password TEXT,
	                               Created_at DATETIME
	                               )""")
			
	        #check for objects older than 3 weeks
	        three_weeks_ago = current_time - timedelta(weeks=3)
	        
	        #only show data that is less than 3 weekes old
	        info = conn.execute(""" 
	                                    SELECT *  FROM Staff_db ORDER BY Id DESC
	                                    """)
	        return info    #return access to the values 
	        conn.commit()
	        conn.close()
        except Error as e:
	        conn.commit()
	        conn.close()
	        flash(f"An Error occured⚠: {e}")  

     #Delete row   
    def delete_row_from_database(self, row_id):
        try:
            conn = sqlite3.connect('hire_admin.db')
            cur = conn.cursor()   
            cur.execute(""" 
	                                DELETE FROM Staff_db WHERE ID = ? 
	                                    """,(row_id))
            flash("Data deleted successfully!!")
            conn.commit()
            conn.close()
        except Error as e:
	        conn.commit()
	        conn.close()
	        flash(f"⚠An Error occured: {e}")
	        
	        
##check is email is blocked
    def is_login_member(self, name, email, password):
    	try:
    		conn = sqlite3.connect('hire_admin.db')
    		cur = conn.cursor()
    		required=[name, email, password]
    		cur.execute(''' SELECT COUNT(*) from Staff_db WHERE Name=?  AND Email=? AND Password = ?''',(required))
    		result = cur.fetchone()
    		return result[0] >0
    	except Error as e:
	        conn.commit()
	        conn.close()
	        flash(f"⚠An Error occured: {e}")
    		
    
    def staff_search(self,search_for):
        try:
	        conn = sqlite3.connect('hire_admin.db')
	        cur = conn.cursor()
	        cur.execute(""" CREATE TABLE if not exists Staff_db (
	                               Id INTEGER PRIMARY KEY AUTOINCREMENT,
	                               Name TEXT,
	                               Email TEXT,
                                   Telphone TEXT,
	                               File_data TEXT,
	                               Filename TEXT,
	                               Content_type TEXT,
	                               Gender TEXT,
	                               Password TEXT,
	                               Created_at DATETIME
	                               )""")
	        
	        #only show data that is less than 3 weekes old
	        info = conn.execute(""" 
	                                    SELECT *  FROM Staff_db WHERE (Email OR Name)=? ORDER BY Id DESC
	                                    """,(search_for,))
	        return info
	        conn.commit()
	        conn.close()
        except Error as e:
	        conn.commit()
	        conn.close()
	        flash(f"An Error occured⚠: {e}")  
	        
	        