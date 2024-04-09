import smtplib
import segno

dates = [
	"01-30-2024", 
	"02-01-2024", 
	"02-06-2024", 
	"02-08-2024", 
	"02-13-2024", 
	"02-15-2024", 
	"02-20-2024", 
	"02-22-2024", 
	"02-27-2024", 
	"02-29-2024",
	"03-05-2024",
	"03-07-2024",
	"03-12-2024",
	"03-26-2024",
	"03-28-2024",
	"04-02-2024",
	"04-04-2024",
	"04-09-2024",
	"04-11-2024",
	"04-16-2024",
	"04-18-2024",
	"04-23-2024",
	"04-25-2024",
	"04-30-2024",
	"05-02-2024",
	"05-07-2024",
	"05-09-2024",
	"05-14-2024",
	]

forms = {}
from apiclient import discovery
from httplib2 import Http
from oauth2client import client, file, tools




SCOPES = "https://www.googleapis.com/auth/forms.body"
DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"

store = file.Storage("token.json")
creds = None
if not creds or creds.invalid:
  flow = client.flow_from_clientsecrets("credentials.json", SCOPES)
  creds = tools.run_flow(flow, store)


form_service = discovery.build(
    "forms",
    "v1",
    http=creds.authorize(Http()),
    discoveryServiceUrl=DISCOVERY_DOC,
    static_discovery=False,
)

for d in dates:
	# Request body for creating a form
	NEW_FORM = {
	    "info": {
	        "title": f'Introduction to Psychopathology Attendance',
	        "documentTitle": f'{d}-Attendance-Psychopathology'
	    },
	}



	LASTNAME_QUESTION = {
	    "requests": [
	        {
	            "createItem": {
	                "item": {
	                    "title": (
	                        "Last Name"
	                    ),
	                    "questionItem": {
	                        "question": {
	                            "required": True,
	                            "textQuestion": {
	                                "paragraph": False,
	                            },
	                        }
	                    },
	                },
	                "location": {"index": 0},
	            }
	        }
	    ]
	}
	FIRSTNAME_QUESTION = {
	    "requests": [
	        {
	            "createItem": {
	                "item": {
	                    "title": (
	                        "First Name"
	                    ),
	                    "questionItem": {
	                        "question": {
	                            "required": True,
	                            "textQuestion": {
	                                "paragraph": False,
	                            },
	                        }
	                    },
	                },
	                "location": {"index": 1},
	            }
	        }
	    ]
	}
	OPTIONAL_QUESTION = {
	    "requests": [
	        {
	            "createItem": {
	                "item": {
	                    "title": (
	                        "Do you have any questions? (Leave Blank if no)"
	                    ),
	                    "questionItem": {
	                        "question": {
	                            "required": False,
	                            "textQuestion": {
	                                "paragraph": False,
	                            },
	                        }
	                    },
	                },
	                "location": {"index": 2},
	            }
	        }
	    ]
	}
	# Creates the initial form
	result = form_service.forms().create(body=NEW_FORM).execute()

	# Request body to add description to a Form
	update = {
	    "requests": [
	        {
	            "updateFormInfo": {
	                "info": {
	                    "description": (
	                        d
	                    )
	                },
	                "updateMask": "description",
	            }
	        }
	    ]
	}





	# Adds the question to the form
	question_setting = (
	    form_service.forms()
	    .batchUpdate(formId=result["formId"], body=LASTNAME_QUESTION)
	    .execute()
	)
	question_setting = (
	    form_service.forms()
	    .batchUpdate(formId=result["formId"], body=FIRSTNAME_QUESTION)
	    .execute()
	)
	question_setting = (
	    form_service.forms()
	    .batchUpdate(formId=result["formId"], body=OPTIONAL_QUESTION)
	    .execute()
	)

	question_setting = (
	    form_service.forms()
	    .batchUpdate(formId=result["formId"], body=update)
	    .execute()
	)

	# Prints the result to show the question has been added
	get_result = form_service.forms().get(formId=result["formId"]).execute()
	forms[d] = get_result["responderUri"]

for form_date in forms:
	qr = segno.make_qr(forms[form_date])
	qr.save(f'{form_date}-qr.png',scale=8,border=10,light="#ffbc00")