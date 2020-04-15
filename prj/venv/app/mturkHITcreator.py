import boto3
from string import Template
from threading import Thread
import xmltodict
import time

import html_content_extractor

#credentials for joo918
ACCESS_KEY = 'AKIAYWS7FAE2GAB6TTJL'
SECRET_KEY = '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'
MTURK_SANDBOX = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'

hitIDs = []
urls_being_validated = []

mturk = boto3.client('mturk',
   aws_access_key_id = ACCESS_KEY,
   aws_secret_access_key = SECRET_KEY,
   region_name='us-east-1',
   endpoint_url = MTURK_SANDBOX #remove for real work
)
#print("I have $" + mturk.get_account_balance()['AvailableBalance'] + " in my Sandbox account")

def request_input(desc, numReq):
   print("I have $" + mturk.get_account_balance()['AvailableBalance'] + " in my Sandbox account")

   print("requesting input urls from mturk workers")
   print("description = " + desc)

   mturk_worker = Template(open('templates/mturk_worker.html', 'r').read())
   mturk_sheet = mturk_worker.substitute(question=desc)

   #print(mturk_sheet)

   new_hit = mturk.create_hit(
      Title = 'Find creative written works on the Internet.',
      Description = 'Given a description, you are asked to find creative written works available on the Internet and provide a URL to the content. More details in the HIT.',
      Keywords = 'provide_reference, creative writing',
      Reward = '8.0',
      MaxAssignments = 500,
      LifetimeInSeconds = 86400,
      AssignmentDurationInSeconds = 600,
      AutoApprovalDelayInSeconds = 28800,
      Question = mturk_sheet
   )

   print("new HIT created: ")
   print(dir(new_hit))
   print("https://workersandbox.mturk.com/mturk/preview?groupId=" + new_hit['HIT']['HITGroupId'])
   print("HITID = " + new_hit['HIT']['HITId'] + " (Use to Get Results)")

   global hitIDs
   hitIDs.append([new_hit['HIT']['HITId'], "reference_provider"])

#need to change
def request_validation(url):
   urls_being_validated.append(url)

   print("I have $" + mturk.get_account_balance()['AvailableBalance'] + " in my Sandbox account")

   print("requesting validation of url(" + url + ") content's creativity")

   mturk_worker = Template(open('templates/mturk_validator.html', 'r').read())
   mturk_sheet = mturk_worker.substitute(link=url)

   # print(mturk_sheet)

   new_hit = mturk.create_hit(
      Title= 'Content creativity validation',
      Description= 'Read written content and validate whether the content is creative.',
      Keywords= 'creativity, validation',
      Reward= '4.0',
      MaxAssignments= 3,
      LifetimeInSeconds= 86400,
      AssignmentDurationInSeconds=600,
      AutoApprovalDelayInSeconds=60 * 60 * 3,
      Question=mturk_sheet
   )

   print("new HIT created: ")
   print(dir(new_hit))
   print("https://workersandbox.mturk.com/mturk/preview?groupId=" + new_hit['HIT']['HITGroupId'])
   print("HITID = " + new_hit['HIT']['HITId'] + " (Use to Get Results)")

   global hitIDs
   hitIDs.append([new_hit['HIT']['HITId'], url])

#parse result XML for each HIT created. Do both reference provision and validation.
def retrieve_result():
   print("retrieving results")
   for hitid in hitIDs:
      worker_results = mturk.list_assignments_for_hit(HITId=hitid[0], AssignmentStatuses=['Submitted'])
      if hitid[1] == 'reference_provider':

         ###########REFERENCE PROVIDER RESULTS

         if worker_results['NumResults'] > 0:
            for assignment in worker_results['Assignments']:
               xml_doc = xmltodict.parse(assignment['Answer'])

               print("Worker's answer was:")

               if type(xml_doc['QuestionFormAnswers']['Answer']) is list:
                  # Multiple fields in HIT layout
                  for answer_field in xml_doc['QuestionFormAnswers']['Answer']:
                     print("For input field: " + answer_field['QuestionIdentifier'])
                     print("Submitted answer: " + answer_field['FreeText'])
                     if not answer_field['FreeText'] in urls_being_validated:
                        print("starting validation for this url")
                        request_validation(answer_field['FreeText'])


               else:
                  # One field found in HIT layout
                  print("For input field: " + xml_doc['QuestionFormAnswers']['Answer']['QuestionIdentifier'])
                  print("Submitted answer: " + xml_doc['QuestionFormAnswers']['Answer']['FreeText'])
                  if not xml_doc['QuestionFormAnswers']['Answer']['FreeText'] in urls_being_validated:
                     print("starting validation for this url")
                     request_validation(xml_doc['QuestionFormAnswers']['Answer']['FreeText'])
         else:
            print("No results ready yet")
      else:

         ############REFERENCE VALIDATOR RESULTS

         if worker_results['NumResults'] == 3:

            numPositive = 0
            for assignment in worker_results['Assignments']:
               xml_doc = xmltodict.parse(assignment['Answer'])

               print("Worker's answer was:")

               if type(xml_doc['QuestionFormAnswers']['Answer']) is list:
                  # Multiple fields in HIT layout
                  for answer_field in xml_doc['QuestionFormAnswers']['Answer']:
                     print("For input field: " + answer_field['QuestionIdentifier'])
                     print("Submitted answer: " + answer_field['FreeText'])
                     if answer_field['QuestionIdentifier'] == 'validation_vote' and (answer_field['FreeText'] == '1' or answer_field['FreeText'] == 1):
                        numPositive = numPositive + 1

               else:
                  # One field found in HIT layout
                  print("For input field: " + xml_doc['QuestionFormAnswers']['Answer']['QuestionIdentifier'])
                  print("Submitted answer: " + xml_doc['QuestionFormAnswers']['Answer']['FreeText'])
            if numPositive >= 2:
               html_content_extractor.addURL(hitid[1])

         else:
            print("Validation not done yet: " + str(worker_results['NumResults']) + "/3")
#wait_for is in hours
def wait_and_retrieve_results(wait_for):
   num_waits = int(wait_for * 60)
   for i in range(num_waits):
      time.sleep(60)
      print(str(i) + " minutes passed")
      retrieve_result()
   #post work


def startCollecting():
   workthread = Thread(target=wait_and_retrieve_results, args=[60])
   workthread.start()


#t = Timer(60.0, retrieve_result)