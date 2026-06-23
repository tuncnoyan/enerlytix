<!--
Idea dump file to consolidate ideas, design options and implementation plans prior to transferring to the spec-kit.
-->
### Constitution
Fill the constitution with requirements for a web app. The app should be windows native. The development should be carried out without admin privileges. Also, the app can be maintained and operated without admin privileges. The application should be containerised natively.
The data security woulod be critical. The database layer should be secure enough to protect data from the unauthorised and external accesses.
Deployments to the production environment should be approved. Similarly, new admin accounts can be added after approvals.

### Specifications
I am building a modern web app to analyse electricity, gas and water usage data. The app should have a landing page that provides basic information about the purpose of the app, also the login and sign up links. Users should sign up and then login with their email addresses to access functionalities of the app. 
- Since this would be a business application, the email address should be part of pre-allowed email domains by admins.
- After successful login, users should be diverted to the home page.
- All pages should be designed according to the corporate branding guidelines (ref. attached file).
- The usage data should be pulled from a specific platform with API.

HOME PAGE
- Users can see the available sites (properties) and available supplies and date ranges for each supply from the selected site.
- To create a report, users should select a site and all or some of the supplies. Then, they should also select the month they want to create the report for.
- The report should be generated when the user click on the "Create Report" button.
- There should also be a link to the "Settings" page and "Sign out" on the home page.
- If the data (the site, supply or the date range) is unavailable in the database, users can upload data by using standard half-hourly and monthly consumption, also invoice data Excel files. (Three standard types)

REPORT PAGE
- There should be various number of analysis and charts depending on the utility type on the report page.
- The report page should be a page with a vertical layout, and to see and work on analysis, users should scroll down on the page.
- There should be a free text and editable comment box beneath each chart.
- When a user finishes all reviews and comment entries, the report can be saved to the database.
- Reports should also be downloadable in client-ready PDF format.

SETTINGS PAGE
- On the settings page, users can change their passwords.

ADMIN PANEL
- There should be an activity log subpage to monitor user activities on the app.
- Admins can see and manage the list of users on a subpage. On that page, admins can reset passwords, delete users, and also invite users.

### Clarify


### Plan


### Tasks


### Analyze


### Implementation