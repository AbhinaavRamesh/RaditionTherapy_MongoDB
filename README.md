<h1>MongoDB Algo engine for Radiation Therapy Similarity Matching Repo</h1>
<br><h2>Project 4: Data Handling and Processing Methods in Radiation Therapy Treatment Planning Decision Support for Head and Neck Cancer Patients Informatics Platform Development </h2>
<h3>Project Leader: Trent Benedick (benedick@usc.edu)
Project Sponsor: Dept of Radiation Medicine, Roswell Park Cancer Center </h3>
<h4> Abhinaav Ramesh, Piwat Wiphanurat, Garima Danidhariya, Mridul Jhawar, Siddarth Ganesh</h4>
<br>
<h3>Slides:</h3>
[BME528_FinalPpt_Group4.pptx](https://github.com/AbhinaavRamesh/RaditionTherapy_MongoDB/files/8565437/BME528_FinalPpt_Group4.pptx)

<br>
<h2> Instructions to Run</h1>
<ol><li> Install the dependacies by cloning the anaconda environment from conda_list.txt</li>
<li>
Run InsertSampleData.py to push sample tables into MongoDB. Things to modify in file:
<ul>
    <li>Path to Stored Data</li>
    <li>MongoDB configuration (New Server URL or change client to connect to local)</li>
</ul>
</li>
<li>Run main.py to execute a sample test for Buffalo Cases 3, to check for the feature extraction parsing from / to the DB</li>
<li> Use GUI managers like Studio 3t to visualize local mogodb client or connect to mongodb atlas cloud</li>
</ol>
<br>
Main Library
<ul>
<li>Pymongo : For connect to the MongoDB server. To retrive and store intermidate data, as well as features after featrue extraction process. - v4.1.1 </li>
</ul>
