# Attendance-rest-api
A Rest Api for attendance management Using Flask and sqlite. It has user side and student side where we can add, delete, Get all the user/student and get selected student/user as well as mark student attendance,getting students according to div and month.

Link to the api: https://attendancetracker.kk-001.repl.co

# END POINTS:

1) /login: login to the site 
2) /user: Get all the users 
3) /user/<public_id>: Get a selected User
4) /user and post: Posting a new user to the database
5) /user/<public_id> and put: promoting a user 
6) /user/<public_id> and delete: For deleting a user 
7) /student and post: posting a new student to the database
8) /student and get: Getting all the students 
9) /student/<string:student_name>: Getting a selected student 
10) /student/<int:month>: getting the whole month attendance
11) /student/delete/<name>: deleting student from the database
12) /<string:divison>: getting students in one Divison
13) /student/attendance/<student_name>/<int:month>/<atte>: for marking the attendance 
  
  
