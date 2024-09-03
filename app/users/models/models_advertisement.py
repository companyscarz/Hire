import sqlite3
from sqlite3 import Error
from datetime import datetime, timedelta
from flask import flash
import geocoder  

current_time = datetime.utcnow()#get current time and date 
g = geocoder.ip('me')
current_country = g.country

##ADvertisemenet
class ADvertisement():
	def __init__(self, email, telphone, link, file_data, filename, content_type, countries, created_at, termination_code):
		self.email = email
		self.telphone = telphone
		self.link = link
		self.file_data = file_data
		self.filename = filename
		self.content_type = content_type
		self.countries = countries
		self.created_at = created_at
		self.termination_code = termination_code
		      
	def add(self):
		try:
			conn = sqlite3.connect('hire.db')
			cur = conn.cursor()
			cur.execute(""" CREATE TABLE if not exists Advertisementdb (
	                               Id INTEGER PRIMARY KEY AUTOINCREMENT,
	                               Email TEXT,
	                               Telphone TEXT,
	                               Link TEXT,
	                               File_data TEXT,
	                               Filename TEXT,
	                               Content_type TEXT,
	                               Countries TEXT,
	                               Created_at DATETIME,
	                               Termination_code TEXT
	                               )""")
	                      ## Store the image data as text (Base64)
			data = [self.email, self.telphone, self.link, self.file_data, self.filename, self.content_type, self.countries, self.created_at, self.termination_code]
			cur.execute(""" 
	                                INSERT INTO Advertisementdb(Email, Telphone, Link, File_data, Filename, Content_type, Countries, Created_at, Termination_code) VALUES(?,?,?,?,?,?,?,?,?)
	                                """, data)
			conn.commit()
			conn.close()
		except Error as e:
			conn.commit()
			conn.close()
			flash(f"⚠An Error occured: {e}")  
    
	def drop(self):
		try:
			conn = sqlite3.connect('hire.db')
			cur = conn.cursor()
			cur.execute(''' DROP TABLE Advertisementdb ''')
			conn.commit()
			conn.close
		except Error as e:
			conn.commit()
			conn.close()
			flash(f"⚠An Error occured: {e}")  
    
	def show(self):
		try:
			conn = sqlite3.connect('hire.db')
			cur = conn.cursor()
			cur.execute(""" CREATE TABLE if not exists Advertisementdb (
	                           Id INTEGER PRIMARY KEY AUTOINCREMENT,
	                           Email TEXT,
	                           Telphone TEXT,
	                           Link TEXT,
	                           File_data TEXT,
	                           Filename TEXT,
	                           Content_type TEXT,
	                           Countries TEXT,
	                           Created_at DATETIME,
	                           Termination_code TEXT
	                           )""")
	            
	        # Check for objects older than 3 weeks
			three_weeks_ago = datetime.utcnow() - timedelta(weeks=3)
	            
	        # Show data that is less than 3 weeks old and matches current country
			
			info = cur.execute(""" 
	                                SELECT * FROM Advertisementdb WHERE Countries = ? AND Created_at > ? 
	                                ORDER BY Id DESC 
	                                """, (current_country, three_weeks_ago,))
			if g.status == 'OK':
				return info
			else:
				flash('⚠Failed to obtain current location! Please check your internet connection.')
			conn.commit()
			conn.close()            
		except Error as e:
			conn.commit()
			conn.close()
			flash(f"⚠An Error occurred: {e}")
        	
	def SHOW(self): ##this shows data in descending order the admin pages
		try:
			conn = sqlite3.connect('hire.db')
			cur = conn.cursor()
			cur.execute(""" CREATE TABLE if not exists Advertisementdb (
	                               Id INTEGER PRIMARY KEY AUTOINCREMENT,
	                               Email TEXT,
	                               Telphone TEXT,
	                               Link TEXT,
	                               File_data TEXT,
	                               Filename TEXT,
	                               Content_type TEXT,
	                               Countries TEXT,
	                               Created_at DATETIME,
	                               Termination_code TEXT
	                               )""")
			
	        #check for objects older than 3 weeks
			three_weeks_ago = current_time - timedelta(weeks=3)
	        
	        #show data that is less than 3 weeks old
			info = cur.execute(""" 
	                                SELECT * FROM Advertisementdb WHERE Created_at > ? ORDER BY Id DESC 
	                                    """,(three_weeks_ago,))                     
			return info
			conn.commit()
			conn.close()
		except Error as e:
			conn.commit()
			conn.close()
			flash(f"⚠An Error occured: {e}")  
 
     #Delete row   
	def delete_row_from_database(self, row_id):
		try:
			conn = sqlite3.connect('hire.db')
			cur = conn.cursor()
			cur.execute(""" 
	                                DELETE FROM Advertisementdb WHERE ID = ? 
	                                    """,(row_id))
			flash("Data deleted successfully!!")
			conn.commit()
			conn.close()
		except Error as e:
			conn.commit()
			conn.close()
			flash(f"⚠An Error occured: {e}")  
 
        	
	def advertisement_search(self,search_advert): ##this shows data in descending order the admin pages
		try:
			conn = sqlite3.connect('hire.db')
			cur = conn.cursor()
			cur.execute(""" CREATE TABLE if not exists Advertisementdb (
	                               Id INTEGER PRIMARY KEY AUTOINCREMENT,
	                               Email TEXT,
	                               Telphone TEXT,
	                               Link TEXT,
	                               File_data TEXT,
	                               Filename TEXT,
	                               Content_type TEXT,
	                               Countries TEXT,
	                               Created_at DATETIME,
	                               Termination_code TEXT
	                               )""")
			
	        #check for objects older than 3 weeks
			three_weeks_ago = current_time - timedelta(weeks=3)
	        
	        #show data that is less than 3 weeks old
			info = cur.execute(""" 
	                                SELECT * FROM Advertisementdb WHERE Created_at > ? AND 
	                                (Email OR Telphone OR Link OR Countries)=? ORDER BY Id DESC 
	                                    """,(three_weeks_ago,search_advert,))                     
			return info
			conn.commit()
			conn.close()
		except Error as e:
			conn.commit()
			conn.close()
			flash(f"⚠An Error occured: {e}")  
			            