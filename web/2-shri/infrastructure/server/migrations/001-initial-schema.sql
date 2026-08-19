-- Up 
CREATE TABLE Builds (id INTEGER PRIMARY KEY AUTOINCREMENT, commithash TEXT, repo TEXT, buildstatus TEXT, exitcode INTEGER, stdout TEXT, stderr TEXT, startdate DATE, enddate DATE, command TEXT);
CREATE TABLE Agents (id INTEGER PRIMARY KEY AUTOINCREMENT, host TEXT, port INTEGER, isbusy BOOLEAN); 

-- Down 
DROP TABLE Builds;
DROP TABLE Agents;