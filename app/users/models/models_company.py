import sqlite3
from sqlite3 import Error
from datetime import datetime, timedelta
from flask import flash
import geocoder  

current_time = datetime.utcnow()#get current time and date 
g = geocoder.ip('me')
current_country = g.country

class COmpany():
	def __init__(self, companyname, companylogo_data, companylogo_filename, companylogo_content_type, companyemail, companyhotline, link, location, seeking, description, gender, education, experience, skills, applying, benefits,  file_data, filename, content_type, countries, created_at, lat, lng, termination_code):
		self.companyname = companyname #for company name
		self.companylogo_data = companylogo_data #for company's logo' data
		self.companylogo_filename = companylogo_filename #for company's logo file name'
		self.companylogo_content_type = companylogo_content_type #for company's logo file type'
		self.companyemail = companyemail # for company's email'
		self.companyhotline = companyhotline #for comapny's hotline'
		self.link = link # for link
		self.location = location # for location
		self.seeking = seeking # what kind of person they want 
		self.description = description # job descritption
		self.gender = gender #for gender
		self.education = education #education level
		self.experience = experience # applicant's experience'
		self.skills = skills # their skills and talents
		self.applying = applying # how to apply
		self.benefits = benefits # what benefits for employees
		self.file_data = file_data # legal document file data
		self.filename = filename # legal document filename
		self.content_type = content_type #legal document file type
		self.countries = countries # list of countries where to post
		self.created_at = created_at #date created
		self.lat = lat #for lat got from geo map
		self.lng = lng #for lng got from geo map
		self.termination_code = termination_code #one will need this code so as to terminate his post
		#you have to send sms and email with termination code to the entered form
        
	def add(self):
		try:
			conn = sqlite3.connect('hire.db')
			cur = conn.cursor()
			cur.execute(""" CREATE TABLE if not exists Companydb(
	                               Id INTEGER PRIMARY KEY AUTOINCREMENT,
	                               Companyname TEXT,
	                               Companylogo_data TEXT, 
	                               Companylogo_filename TEXT, 
	                               Companylogo_content_type TEXT,
	                               Companyemail TEXT, 
	                               Companyhotline TEXT, 
	                               Link TEXT,
	                               Location TEXT, 
	                               Seeking TEXT, 
	                               Description TEXT, 
	                               Gender TEXT, 
	                               Education TEXT, 
	                               Experience TEXT, 
	                               Skills TEXT, 
	                               Applying TEXT, 
	                               Benefits TEXT,
	                               File_data TEXT,
	                               Filename TEXT,
	                               Content_type TEXT,
	                               Countries TEXT,
	                               Created_at DATETIME,
	                               Lat FLOAT,
	                               Lng FLOAT,
	                               Termination_code TEXT
	                               )""")
			data = [self.companyname, self.companylogo_data, self.companylogo_filename, self.companylogo_content_type, self.companyemail, self.companyhotline, self.link, self.location, self.seeking, self.description, self.gender, self.education, self.experience, self.skills, self.applying, self.benefits, self.file_data, self.filename, self.content_type, self.countries, self.created_at, self.lat, self.lng, self.termination_code]
			cur.execute(""" 
	                                INSERT INTO Companydb(Companyname, Companylogo_data, Companylogo_filename, Companylogo_content_type, Companyemail, Companyhotline, Link, Location, Seeking, Description, Gender, Education, Experience, Skills, Applying, Benefits, File_data, Filename, Content_type, Countries, Created_at, Lat, Lng, Termination_code) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
	            """, data)
			conn.commit()
			conn.close()
		except Error as e:
			flash(f"⚠An Error occured: {e}")  
            
	def drop(self):
		try:
			conn = sqlite3.connect('hire.db')
			cur = conn.cursor()
			cur.execute(''' DROP TABLE Companydb ''')
			conn.commit()
			conn.close()
		except Error as e:
			flash(f"⚠An Error occured: {e}")  
    
	def show(self):
		try:
			conn = sqlite3.connect('hire.db')
			cur = conn.cursor()
			cur.execute(""" CREATE TABLE if not exists Companydb (
	                               Id INTEGER PRIMARY KEY AUTOINCREMENT,
	                               Companyname TEXT,
	                               Companylogo_data TEXT, 
	                               Companylogo_filename TEXT, 
	                               Companylogo_content_type TEXT, 
	                               Companyemail TEXT, 
	                               Companyhotline TEXT, 
	                               Link TEXT,
	                               Location TEXT, 
	                               Seeking TEXT, 
	                               Description TEXT, 
	                               Gender TEXT, 
	                               Education TEXT, 
	                               Experience TEXT, 
	                               Skills TEXT, 
	                               Applying TEXT, 
	                               Benefits TEXT,
	                               File_data TEXT,
	                               Filename TEXT,
	                               Content_type TEXT,
	                               Countries TEXT,
	                               Created_at DATETIME,
	                               Lat FLOAT,
	                               Lng FLOAT,
	                               Termination_code TEXT
	                               )""")
					
	        #check for objects older than 3 weeks
			three_weeks_ago = current_time - timedelta(weeks=3)
	        
			info = conn.execute(""" 
	                                    SELECT *  
										FROM Companydb
										WHERE Countries = ? AND Created_at > ? 
										ORDER BY Id DESC
	                                    """,(current_country,three_weeks_ago,))      
			results = info.fetchall()
			if g.status == 'OK':
				return info
			else:
				#flash('⚠Failed to obtain current location! Please check your internet connection.')
				pass
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
	        				DELETE FROM Companydb WHERE ID = ? 
	                    """,(row_id))
			flash("Data deleted successfully!!")
			conn.commit()
			conn.close()
		except Error as e:
			flash(f"⚠An Error occured: {e}")  

####search by company name
	def search_for_company(self,search_company):
		try:
			conn = sqlite3.connect('hire.db')
			cur = conn.cursor()
			cur.execute(""" CREATE TABLE if not exists Companydb (
	                               Id INTEGER PRIMARY KEY AUTOINCREMENT,
	                               Companyname TEXT,
	                               Companylogo_data TEXT, 
	                               Companylogo_filename TEXT, 
	                               Companylogo_content_type TEXT, 
	                               Companyemail TEXT, 
	                               Companyhotline TEXT, 
	                               Link TEXT,
	                               Location TEXT, 
	                               Seeking TEXT, 
	                               Description TEXT, 
	                               Gender TEXT, 
	                               Education TEXT, 
	                               Experience TEXT, 
	                               Skills TEXT, 
	                               Applying TEXT, 
	                               Benefits TEXT,
	                               File_data TEXT,
	                               Filename TEXT,
	                               Content_type TEXT,
	                               Countries TEXT,
	                               Created_at DATETIME,
	                               Lat FLOAT,
	                               Lng FLOAT,
	                               Termination_code TEXT
	                               )""")
					
	        #check for objects older than 3 weeks
			three_weeks_ago = current_time - timedelta(weeks=3)
	        
			info = conn.execute("""
				SELECT *  FROM Companydb WHERE Countries = ? AND Created_at > ? AND 
          	(Companyname OR Companyemail OR Location OR 
           	Seeking OR Gender OR Education OR Experience OR 
           	Skills OR Benefits )=?
    			ORDER BY Id DESC""", (current_country, three_weeks_ago, search_company,))
			
			results = info.fetchall()	
			if g.status == 'OK':
				return results
			else:
				pass
			conn.commit()
			conn.close()
		except Error as e:
			flash(f"⚠An Error occured: {e}")	  
			
	      