from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.template import Template, Context

# importing other views.py files

# importing models.py files.
from loginapp import models as login_models
from profileapp import models as profile_models

# importing security modules.
from django.middleware import csrf
import bcrypt
from loginapp import validation_check

# other handling functions.
from backend_functions import backend_handling_functions, otp_handling


def homePage(request):
	"home page: a static file."
	if request.POST or len(request.POST) > 0:
		return HttpResponse('''<body><meta http-equiv="refresh" content='0; url="/"'/></body>''')
	return render(request, "home_page.html")


def signUpPage(request):
	"asking for signup page"
	if request.POST or len(request.POST) > 0:
		return HttpResponse('''<body><meta http-equiv="refresh" content='0; url="/signup/"'/></body>''')

	# Sessions and tokens.
	csrf_token = csrf.get_token(request)
	return render(request, 'signup_page.html', {"csrf_token": csrf_token , "error_signing" : False, "user_exist": False})


def signUpPosted(request):
	"action on posted signup page"
	
	# Security check for method-interchange vaulnerablity: https://blog.nvisium.com/method-interchange-forgotten
	if request.GET or len(request.GET) > 0:
		return HttpResponse('''<body><meta http-equiv="refresh" content='0; url="/signup/"'/></body>''')

	# Sessions and Tokens.
	csrf_token = csrf.get_token(request)

	# Incoming data.
	input_data = request.POST

	"""Default values are such that, if the value (for a key) is not in the request.POST (dictionary-like), then
		the validation will not be True. Thus lead to "error_signing".
		This above technique resolve the issue of middleman attack where data is tempered or removed (while sending
		request) by tools like burpsuite."""

	first_name, last_name = input_data.get("first_name", "").strip().lower(), input_data.get("last_name", "").strip().lower()
	first_name_check = validation_check.nameCheck(first_name)
	last_name_check = validation_check.nameCheck(last_name)

	user_class, user_section = input_data.get("user_class", "0").strip(), input_data.get("user_section", "NaN").strip()
	user_class_check = validation_check.classCheck(user_class)
	user_section_check = validation_check.sectionCheck(user_section)

	user_contact, r_number = input_data.get("contact_detail", "0").strip(), input_data.get("r_number", "0").strip()
	contact_check = validation_check.contactCheck(user_contact)
	r_number_check = validation_check.rCheck(r_number)


	school_name, user_category = input_data.get("school_name", "").strip().lower(), input_data.get("user_category", "").strip().upper()
	school_name_check = validation_check.schoolNameCheck(school_name)
	user_category_check = validation_check.categoryCheck(user_category)


	email_address, password = input_data.get("email_address", "").strip().lower(), input_data.get("pswd", "").strip()
	password_check = validation_check.passwordCheck(password)
	email_address_check = validation_check.emailCheck(email_address)


	if not (first_name_check and last_name_check and user_class_check and user_section_check and contact_check and r_number_check and school_name_check and user_category_check and email_address_check and password_check):
		# handling tempered data.
		# The incoming data was corrupted (maybe using burpsuite.) (This is because, all the above validations were done at frontend, but still the value arent valid values.)
		return render(request, 'signup_page.html', {"csrf_token": csrf_token , "error_signing" : True, "user_exist": False})

	"""----------Now all the input values are valid.---------------"""

	# data formatting.
	first_name = first_name[0].upper() + first_name[1:]
	last_name = last_name[0].upper() + last_name[1:]
	user_section = user_section.upper() + "S"
	if len(user_class) != 2:
		user_class = "0" + user_class
	user_category = user_category.upper()

	"""----------password encryption.---------------"""
	# password hashing and salting to be done here.
	# Refer Here: https://security.stackexchange.com/questions/8596/https-security-should-password-be-hashed-server-side-or-client-side
	salt = bcrypt.gensalt()
	byte_password = password.encode('utf-8')
	hashed_password = bcrypt.hashpw(byte_password, salt)

	if len(login_models.USER_SIGNUP_DATABASE.objects.filter(email_address=email_address)) > 0:
		"""----------user already exist.---------------"""
		if not login_models.USER_SIGNUP_DATABASE.objects.filter(email_address=email_address)[0].verfied_user:
			"""but not verified"""
			return HttpResponse('''<body><script>alert("User already exist! But not verfied. Go to login page and verify.")</script><meta http-equiv="refresh" content="0; url='/login/'"></body>''')
		"""verified"""
		return render(request, 'signup_page.html', {"csrf_token":csrf_token , "error_signing" : False, "user_exist": True})
	
	"""----------Now it is confirmed the user is new.---------------"""
	
	# backend database working
	class_course_field = backend_handling_functions.auto_assign_course(user_class, user_section, user_category)
	
	if user_category == "TEACHER":
		school_data = login_models.TEACHER_CODE_MAPPING.objects.filter(teacher_email=email_address)
		if len(school_data) == 0:
			return HttpResponse('''<body><script>alert("User specified email, is not a teacher's email (as given to us by the school)")</script><meta http-equiv="refresh" content="0; url='/signup/'"></body>''')

		school_data = school_data[0]
		assigned_class = school_data.teacher_assigned_class
		assigned_section = school_data.teacher_assigned_section
		if assigned_section != user_section or assigned_class != user_class:
			return HttpResponse('''<body><script>alert("Teacher inserted class/section, is not the same as given by the school's data.")</script><meta http-equiv="refresh" content="0; url='/signup/'"></body>''')

	try:
		if user_category == "STUDENT":
			connected_to = None
		else:
			connected_to = login_models.TEACHER_CODE_MAPPING.objects.get(teacher_email=email_address)
		
		setting_user = login_models.USER_SIGNUP_DATABASE(first_name = first_name, last_name = last_name, user_class=user_class, user_section=user_section, user_contact=user_contact, user_r_number=r_number, school_name = school_name, user_category=user_category, email_address=email_address, password=hashed_password, class_course_field=class_course_field, connected_to=connected_to)
		setting_profile = profile_models.USER_PROFILE_DATABASE(user_signup_db_mapping = setting_user)
		setting_user.save()
		setting_profile.save()
	except:
		"""----------Some error while setting user.---------------"""
		return render(request, 'signup_page.html', {"csrf_token":csrf_token , "error_signing" : True, "user_exist": False})
	
	"""----------User Succesfully Created. But need to verify still---------------"""
	status = otp_handling.otp_sending_handling(email_address, user_category)
	if not status:
		return render(request, 'signup_page.html', {"csrf_token":csrf_token , "error_signing" : True, "user_exist": False})
	
	request.session['user_email_for_otp'] = email_address
	return render(request, 'verify_otp.html', {"given_user": setting_user})


def signupOTPVerfied(request):
	if request.POST or len(request.POST) > 0:
		return HttpResponse('''<body><script>alert("Some error occured from user side.")</script><meta http-equiv="refresh" content='0; url="/signup/"'/></body>''')
	
	active_status = False
	if request.session.has_key('user_email_for_otp') and not (request.session["user_email_for_otp"] == None):
		active_status = True
		email_of_request = request.session['user_email_for_otp']

	if active_status:
		input_data = request.GET

		received_otp = input_data.get("input_otp", "0")

		if len(received_otp) != 8 or (not received_otp.isnumeric()):
			return HttpResponse('''<body><script>alert("Invalid OTP entered")</script><meta http-equiv="refresh" content='0; url="/login/"'/></body>''')
		
		selected_user = login_models.USER_SIGNUP_DATABASE.objects.get(email_address=email_of_request)
		user_category = selected_user.user_category
		first_name_only = selected_user.first_name
		verify = otp_handling.otp_receiving_handling(email_of_request, received_otp, user_category)
		if verify:
			selected_user.verfied_user = True
			selected_user.save()
			del request.session['user_email_for_otp']
			if user_category == "STUDENT":
				removing_entry = login_models.OTP_DATABASE.objects.get(assigned_email=email_of_request)
				removing_entry.delete()
			if user_category == "TEACHER":
				teacher_is_assigned = login_models.TEACHER_CODE_MAPPING.objects.get(teacher_email=email_of_request)
				teacher_is_assigned.activation_status = True
				teacher_is_assigned.save()
			return render(request, 'signup_success.html', {"full_name": first_name_only})
		else:
			return HttpResponse('''<body><script>alert("Incorrect OTP. Retry again")</script><meta http-equiv="refresh" content='0; url="/login/"'/></body>''')
	else:
		return HttpResponse('''<body><script>alert("Some error occured from user side. (Such as, user is not created yet.)")</script><meta http-equiv="refresh" content='0; url="/signup/"'/></body>''')

def resendOTPVerify(request):
	if request.POST or len(request.POST) > 0:
		return HttpResponse('''<body><script>alert("Some error occured from user side.")</script><meta http-equiv="refresh" content='0; url="/login/"'/></body>''')

	active_status = False
	if request.session.has_key('user_email_for_otp') and not (request.session["user_email_for_otp"] == None):
		active_status = True
		email_of_request = request.session['user_email_for_otp']

	if active_status:
		selected_user = login_models.USER_SIGNUP_DATABASE.objects.filter(email_address=email_of_request)[0]
		user_category = selected_user.user_category
		status = otp_handling.otp_sending_handling(email_of_request, user_category)
		if not status:
			return render(request, 'signup_page.html', {"csrf_token":csrf_token , "error_signing" : True, "user_exist": False})
		return render(request, 'verify_otp.html', {"given_user": selected_user})
	else:
		return HttpResponse('''<body><script>alert("Some error occured from user side. (Such as user is already verfied)")</script><meta http-equiv="refresh" content='0; url="/login/"'/></body>''')

def contactPage(request):
	if request.POST or len(request.POST) > 0:
		return HttpResponse('''<body><meta http-equiv="refresh" content='0; url="/contact/"'/></body>''')
	# Sessions and tokens.
	csrf_token = csrf.get_token(request)
	return render(request, 'contact_page.html', {"csrf_token":csrf_token , "query_submitted": False, "upload_error": False})

def contactPageSubmitted(request):
	if request.GET or len(request.GET) > 0:
		return HttpResponse('''<body><script>alert("Some Error occured: Incorrect HTTP Request Method")</script><meta http-equiv="refresh" content='0; url="/contact/"'/></body>''')

	# Sessions and tokens.
	csrf_token = csrf.get_token(request)

	input_data = request.POST

	# need to change, as we are not using url anymore but we are using name.
	query_email_address = input_data.get("query_email", "").strip().lower()
	query_email_check = validation_check.emailCheck(query_email_address)

	query_name = input_data.get("query_name", None).strip()
	query_name_check = validation_check.nameCheck(query_name)

	query_description = input_data.get("query_description", "").strip()
	query_content_check = validation_check.schoolNameCheck(query_description) # As it acts similar to a school name.


	if not (query_email_check and query_content_check and query_name_check):
		# handling tempered data.
		return render(request, 'contact_page.html', {"csrf_token": csrf_token , "query_submitted": False, "upload_error": True})

	try:
		setting_query = login_models.QueryStore(query_email_address = query_email_address, query_name = query_url, query_description = query_description)
		setting_query.save()
	except:
		return render(request, 'contact_page.html', {"csrf_token": csrf_token , "query_submitted": False, "upload_error": True})

	return render(request, 'contact_page.html', {"csrf_token": csrf_token , "query_submitted": True, "upload_error": False})


def loginPage(request):
	if request.POST or len(request.POST) > 0:
		return HttpResponse('''<body><meta http-equiv="refresh" content='0; url="/login/"'/></body>''')
	
	# Sessions and tokens.
	csrf_token = csrf.get_token(request)
	active_status = False
	# getting user_id from session token.
	user_id = None
	if request.session.has_key('user_id'):
		active_status = True
		user_id = request.session["user_id"]
	if active_status:
		return HttpResponse(f'''<body><meta http-equiv="refresh" content='0; url="/profile/"'/></body>''')
	return render(request, "login_page.html", {"csrf_token":csrf_token, "error_login":False, "user_not_exist":False, "invalid_password":False})


def loginPageCheck(request):
	if request.GET or len(request.GET) > 0:
		return HttpResponse('''<body><meta http-equiv="refresh" content='0; url="/login/"'/></body>''')
	
	# Sessions and tokens.
	csrf_token = csrf.get_token(request)
	active_status = False
	# getting user_id from session token.
	user_id = None
	if request.session.has_key('user_id'):
		active_status = True
		user_id = request.session["user_id"]
	if active_status:
		return HttpResponse(f'''<body><meta http-equiv="refresh" content='0; url="/profile/"'/></body>''')

	
	Authentication = False
	input_data = request.POST

	enter_user_name = input_data.get("entered_email", False)
	enter_user_name_check = validation_check.emailCheck(enter_user_name)

	enter_password = input_data.get("entered_password", False)
	enter_password_check = validation_check.passwordCheck(enter_password)

	if not(enter_user_name_check and enter_password_check):
		# hadling tempered data.
		return render(request, "login_page.html", {"csrf_token":csrf_token, "error_login" : True, "user_not_exist": False, "invalid_password":True})

	if len(login_models.USER_SIGNUP_DATABASE.objects.filter(email_address=enter_user_name)) == 0:
		# User does not exist.
		return render(request, "login_page.html", {"csrf_token":csrf_token, "error_login" : False, "user_not_exist": True, "invalid_password":False})
		
	"""----------password encryption.---------------"""
	byte_enter_password = enter_password.encode('utf-8')

	extracted_user = login_models.USER_SIGNUP_DATABASE.objects.get(email_address=enter_user_name)
		
	if bcrypt.checkpw(byte_enter_password, extracted_user.password):
		Authentication = True

	if Authentication:
		if not extracted_user.verfied_user:
			status = otp_handling.otp_sending_handling(enter_user_name, extracted_user.user_category)
			if not status:
				return render(request, 'signup_page.html', {"csrf_token":csrf_token , "error_signing" : True, "user_exist": False})
			request.session['user_email_for_otp'] = enter_user_name
			return render(request, 'verify_otp.html', {"given_user": extracted_user})
		else:
			request.session['user_id'] = extracted_user.id
			return HttpResponse(f'''<body><meta http-equiv="refresh" content='0; url="/profile/"'/></body>''')
	else:
		return render(request, "login_page.html", {"csrf_token":csrf_token, "error_login" : False, "user_not_exist": False, "invalid_password": True})

def logoutPage(request):
	if request.POST or len(request.POST) > 0:
		return HttpResponse(f'''<body><meta http-equiv="refresh" content='0; url="/login/"'/></body>''')
	
	# Sessions and tokens.
	csrf_token = csrf.get_token(request)
	active_status = False
	# getting user_id from session token.
	user_id = None
	if request.session.has_key('user_id'):
		active_status = True
		user_id = request.session["user_id"]
	
	if active_status:
		del request.session["user_id"]
	return HttpResponse(f'''<body><meta http-equiv="refresh" content='0; url="/login/"'/></body>''')

def forgotPasswordPage(request):
	if request.POST or len(request.POST) > 0:
		return HttpResponse(f'''<body><meta http-equiv="refresh" content='0; url="/login/"'/></body>''')

	# Sessions and tokens.
	csrf_token = csrf.get_token(request)

	return render(request, "login_forgotpass.html")

def forgotPasswordSendEmail(request):
	if request.GET or len(request.GET) > 0:
		return HttpResponse(f'''<body><meta http-equiv="refresh" content='0; url="/login/"'/></body>''')
	input_data = request.POST

	rec_email = input_data.get("forgot_email", "")
	rec_email_check = validation_check.emailCheck(rec_email)

	if not rec_email_check:
		return HttpResponse(f'''<body><script>alert("Not a valid Email address.")</script><meta http-equiv="refresh" content='0; url="/login/"'/></body>''')
	
	extract_user__user_signup_database = login_models.USER_SIGNUP_DATABASE.objects.filter(email_address=rec_email)

	if not (len(extract_user__user_signup_database) > 0):
		return HttpResponse(f'''<body><script>alert("No user with this email exist. Create a new user.")</script><meta http-equiv="refresh" content='0; url="/signup/"'/></body>''') 

	extract_user__user_signup_database = extract_user__user_signup_database[0]

	status = otp_handling.otp_sending_handling(rec_email, extract_user__user_signup_database.user_category)
	if not status:
		return HttpResponse(f'''<body><script>alert("Some error occured. Try again later or Contact us.")</script><meta http-equiv="refresh" content='0; url="/login/"'/></body>''') 
	
	request.session['forgot_email_for_otp'] = email_address
	return render(request, 'forgot_otp.html')

def forgotPasswordOTPVerify(request):
	pass
	# if all checks are passed, return a page for change password going to link, /forgot/change/
	#request.session["allowchange"] = email
def changePassword(request):
	pass
	# check using "allowchange" if True then only