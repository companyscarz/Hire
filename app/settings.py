import secrets

from users.models.models_company import COmpany
from users.models.models_applicant import APplicant
from users.models.models_advertisement  import ADvertisement
from admin.models.models_staff import STaff
from users.models.models_block import BLock
from users.models.models_about  import ABout

class Config():
	SECRET_KEY = secrets.token_hex(4020)
	DEBUG = True
	#DATABASE_URI
	CODE_1="*ouglas582888"
	CODE_2="*ouglas162333"
	RECAPTCHA_PUBLIC_KEY = "6Lf9j20pAAAAAKTR5MBCGeF6VgPyxguYV0jXjEqD"
	RECAPTCHA_PRIVATE_KEY = "6Lf9j20pAAAAAIe5oVo8cG4w7SUSCPHQgPuqKVYy"
	Openai = "sk-proj-5W2UbjdO0R9UarVR2RFZT3BlbkFJXVhviRS5rRFd2wOsWJu2"
	mapbox='pk.eyJ1IjoiZG91Z2xhc3NjYXJ6IiwiYSI6ImNsd2txeTJjcTBnencyaXA4azB4dHlwY3QifQ.5k8f4cxAFDluxWeiqyPFdw'
	host='0.0.0.0' 
	port=8080

	block = BLock('0','1')
	suggestions = ABout('0','1') 
	advertisements = ADvertisement('0','1','2','3','4', '5','6','7','8')
	applications = APplicant('0','1','2','3','4','5','6','7','8','9','10','11','12','13','14')
	opportunities = COmpany('0','1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20','21','22','23')
	members = STaff('douglas','douglas@gmail.com','2','3','4','5','6','password','8')

#block.show()
#suggestions.show()
#advertisements.show()
#applications.show()
#opportunities.show()
#members.show()
