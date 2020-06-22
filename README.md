# So You Think You Can Cater

Name: Eric Laslo

Pitt ID: ERL67@pitt.edu


## Installation

1. export FLASK_APP=catering.py && flask initdb && flask run

2. http://127.0.0.1:5000/



## Running the App

Initialize Database Automatically:

Set REBUILD_DB = True at beginning of program. 
	If catering.db exists it will be regenerated.
	If it doesn't exist it will be created.  No need for CLI.
	Tables will be populated with sample data in the model
	
	
Set FDEBUG on line 2 to true if you want to use the debug toolbar



visit /db/ to view all objects in the database for testing purposes, also available from owners page
colors are generated based on a hash of the innerHTML, so each page will be different