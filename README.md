# README #

### What is this repository for? ###

This application is intended for use in a Mastery Learning environment, where learners take and re-take a variety of quizzes. 
The instructor dashboard allows for insight into learner performance, individually and on aggregate.

## Set Up

- Install Django. This can be done via pip: `pip install Django`
- Initialize the secret_key field in /ml_quiz_app/config.py to a random string of 50 characters
- Run the following commands:
    - `python manage.py makemigrations quiz`
    - `python manage.py makemigrations dashboard`
    - `python manage.py migrate`

#### Development
- Run the command `python manage.py runserver` to run locally.

#### Production
- Set-up in production environment is dependent on server configuration. View the [Django deployment documentation](https://docs.djangoproject.com/en/2.2/howto/deployment/) for more information.
- Static file serving will also need to be configured in order to view quiz files through the instructor dashboard. See the [Django documentation](https://docs.djangoproject.com/en/2.2/howto/static-files/deployment/) for various approaches to this.

## Configuration & Use
- Answers keys to quizzes are contained in /import_data/rubric.csv. 
Once updated, the rubric can be imported via the button on the dashboard home page or by running the command `python manage.py import_rubric`.
An entry for a quiz must be added to the rubric and imported before learners can take that quiz through the system.
- Required quiz topics can be specified in the REQUIRED_QUIZZES field in /config/grade_config.py.
- Feedback messages are found in the /import_data/feedback/ directory. 
One CSV should be added for each topic; filename should be uppercase topic ID. 
Each quiz question should be matched with exactly one feedback message. 
Feedback messages can be imported via the button on the dashboard home page or by running the command `python manage.py import_feedback`.
- Sample quiz information can be found in the rubric and feedback files. Deleting these rows from the rubric.csv will remove these quizzes from your system.
- A class list can be added at /import_data/classlist.csv. The restrict_student_classlist field in /config/dashboard_config.py can be set to true to allow only students in the classlist to take quizzes.
- Unmarked quiz submissions can be marked via the "Update Grades" button on the dashboard home page, or by running the command `python manage.py mark_written n`. 
To mark all submissions, including re-marking those already marked, run `python manage.py mark_written y`.
