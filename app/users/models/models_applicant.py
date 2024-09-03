import sqlite3
from sqlite3 import Error
from datetime import datetime, timedelta
from flask import flash
import geocoder  

current_time = datetime.utcnow()#get current time and date 
g = geocoder.ip('me')
current_country = g.country

###applicant database       
class APplicant():
	def __init__(self, name, email, telphone, gender, position, interest, education, experience, skills,  file_data, filename, content_type, countries, created_at, termination_code):
		self.name = name
		self.email = email 
		self.telphone = telphone 
		self.gender = gender 
		self.position = position 
		self.interest = interest 
		self.education = education 
		self.experience = experience 
		self.skills = skills 
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
			cur.execute(""" CREATE TABLE if not exists Applicantdb (
	                               Id INTEGER PRIMARY KEY AUTOINCREMENT,
	                               Name TEXT,
	                               Email TEXT,
	                               Telphone TEXT, 
	                               Gender TEXT, 
	                               Position TEXT, 
	                               Interest TEXT, 
	                               Education TEXT, 
	                               Experience TEXT, 
	                               Skills TEXT, 
	                               File_data TEXT,
	                               Filename TEXT,
	                               Content_type TEXT, 
	                               Countries TEXT, 
	                               Created_at DATETIME,
	                               Termination_code TEXT
	                               )""")
			data = [self.name, self.email, self.telphone, self.gender, self.position, self.interest, self.education, self.experience, self.skills, self.file_data, self.filename, self.content_type, self.countries, self.created_at, self.termination_code]
			cur.execute(""" 
	                                INSERT INTO Applicantdb (Name, Email, Telphone, Gender, Position, Interest, Education, Experience, Skills,File_data, Filename, Content_type, Countries, Created_at,Termination_code) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
	            		""", data)
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
	                       DELETE FROM Applicantdb WHERE ID = ? 
	                    """,(row_id))
			flash("Data deleted successfully!!")
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
			cur.execute(''' DROP TABLE Applicantdb ''')
			conn.commit()
			conn.close()
		except Error as e:
			conn.commit()
			conn.close()
			flash(f"⚠An Error occured: {e}")  
    
	def show(self):
		try:
			conn = sqlite3.connect('hire.db')
			cur = conn.cursor()
			cur.execute(""" CREATE TABLE if not exists Applicantdb (
	                               Id INTEGER PRIMARY KEY AUTOINCREMENT,
	                               Name TEXT,
	                               Email TEXT,
	                               Telphone TEXT, 
	                               Gender TEXT, 
	                               Position TEXT, 
	                               Interest TEXT, 
	                               Education TEXT, 
	                               Experience TEXT, 
	                               Skills TEXT, 
	                               File_data TEXT,
	                               Filename TEXT,
	                               Content_type TEXT,
	                               Countries TEXT, 
	                               Created_at DATETIME,
	                               Termination_code TEXT
	                               )""")
			
	        #check for objects older than 3 weeks
			three_weeks_ago = current_time - timedelta(weeks=3)
	        
	        #only show data that is less than 3 weekes old
			cur.execute(""" 
	                       SELECT *  FROM Applicantdb
	                       WHERE Countries = ? AND Created_at > ?
						   ORDER BY Id DESC 
	                    """,(current_country,three_weeks_ago,))
			info = cur.fetchall()
			if g.status == 'OK':
				return info
			else:
				#flash('⚠Failed to obtain current location! Please check your internet connection.')
				pass
			conn.commit()
			conn.close()
		except Error as e:
			conn.commit()
			conn.close()
			flash(f"⚠An Error occured: {e}")  

	def search_for_applicant(self,search_applicant):
		try:
			conn = sqlite3.connect('hire.db')
			cur = conn.cursor()
			cur.execute(""" CREATE TABLE if not exists Applicantdb (
	                               Id INTEGER PRIMARY KEY AUTOINCREMENT,
	                               Name TEXT,
	                               Email TEXT,
	                               Telphone TEXT, 
	                               Gender TEXT, 
	                               Position TEXT, 
	                               Interest TEXT, 
	                               Education TEXT, 
	                               Experience TEXT, 
	                               Skills TEXT, 
	                               File_data TEXT,
	                               Filename TEXT,
	                               Content_type TEXT,
	                               Countries TEXT, 
	                               Created_at DATETIME,
	                               Termination_code TEXT
	                               )""")
			
	        #check for objects older than 3 weeks
			three_weeks_ago = current_time - timedelta(weeks=3)
	        
	        #only show data that is less than 3 weekes old
			cur.execute(""" 
	                       SELECT *  FROM Applicantdb
	                       WHERE Countries = ? AND Created_at > ? AND 
	                       (Name OR Email OR Gender OR Position OR Education OR Experience OR Skills)=?
						   ORDER BY Id DESC 
	                    """,(current_country,three_weeks_ago, search_applicant,))
			info = cur.fetchall()
			if g.status == 'OK':
				return results
			else:
				#flash('⚠Failed to obtain current location! Please check your internet connection.')
				pass
			conn.commit()
			conn.close()
		except Error as e:
			conn.commit()
			conn.close()
			flash(f"⚠An Error occured: {e}")  