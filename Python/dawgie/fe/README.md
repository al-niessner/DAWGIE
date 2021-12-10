# REST API

Describes the REST API (endpoints) that DAWGIE provides to access the data it manages. Inputs to the REST API are mostly if not all URL parameters. The outputs are HTML, JSON or text depending on the endpoint.

Each endpoint begins with `/app`, short for application, to identify the REST API that can be programatically accessed. These endpoints are different than the endpoints that return fixed pages like /pages/index.html that is the front page. The endpoints are then further subdivided into logical groups: `/app/db`, `/app/filter`, `/app/pl`, `/app/schedule`, `/app/search`. There are several endpoints that do not fall into these logical groups as well.

- `/app/db` direct access to the data keys (target names, task names, etc)
- `/app/filter` restrict searches in the data base
- `/app/pl` direct access to information about the state of the piupeline
- `/app/schedule` direct access to the schedule as DAWGIE currently understands it
- `/app/search` search the database to select specific data keys (target names, task names, etc)

The endpoints are listed in alphabetical order and documented as:

---

## Endpoint (GET/POST) (HTML/JSON/text)
### Description
actual description

### Inputs
- varname:type  
  description

### Outputs
- varname:type  
  description
    
### Example

```
curl command
and results
```

---


"""Note: all examples are using the Algorithm Engine (AE) defined in DAWGIE/Test/ae"""

"""Note: ${baseurl} should be something like `http://localhost:8080`"""

## TOC

- [`/app/changeset.txt`](#appchangesettxt-get-text)
- [`/app/db/item`](#appdbitem-get-html)
- [`/app/db/lockview`](#appdblockview-get)
- [`/app/db/prime`](#appdbprime-get)
- [`/app/db/targets`](#appdbtargets-get)
- [`/app/db/versions`](#appdbversions-get)
- [`/app/filter/admin`](#appfilteradmin-get)
- [`/app/filter/dev`](#appfilterdev-get)
- [`/app/filter/user`](#appfilteruser-get)
- [`/app/pl/log`](#apppllog-get)
- [`/app/pl/state`](#appplstate-get)
- [`/app/run`](#apprun-post)
- [`app/schedule/crew-get`](#ppschedulecrew-get-get)
- [`/app/schedule/doing`](#appscheduledoing-get)
- [`/app/schedule/events`](#appscheduleevents-get)
- [`/app/schedule/failure`](#appschedulefailure-get)
- [`/app/schedule/success`](#appschedulesuccess-get)
- [`/app/schedule/tasks`](#appscheduletasks-get)
- [`/app/schedule/todo`](#appscheduletodo-get)
- [`/app/search/completion/sv`](#appsearchcompletion/sv-get)
- [`/app/search/completion/tn`](#appsearchcompletion/tn-get)
- [`/app/search/ri`](#appsearchri-get)
- [`/app/search/sv`](#appsearchsv-get)
- [`/app/search/tn`](#appsearchtn-get)
- [`/app/state/status`](#appstatestatus-get)
- [`/app/submit`](#appsubmit-post)
- [`app/versions`](#ppversions-get`)


## `/app/changeset.txt` (GET) (text)
### Description

Returns the GIT changeset ID of the Algorithm Engine (AE) -- aka science code -- that this server is using.

### Inputs
_no inputs_

### Outputs
- _unnamed_:string  
  the GIT changeset ID

### Example

```
curl -X GET "${baseurl}/app/changeset.txt"
baff80d5ecb08ef1370507fb055759973bc462f9
```

## `/app/db/item` (GET) (HTML)
### Description

Render a specific state vector to HTML.

### Inputs
- path:string  
  '.' separate complete name of a state vector.

### Outputs
 - _unnamed_:string  
   a complete HTML page

### Example

```
curl -X GET "${baseurl}/app/db/item?path="
abc
```

## `/app/db/lockview` (GET) (JSON)
### Description

When using the shelf database system, locks are required to synchronize access to the database (postgresql provides this natively). At times, it was important to understand which tasks had locks on the database. This call returns the list of tasks that hold locks on the database.

### Inputs
_no inputs_

### Outputs
- tasks:list(string)  
  each element of tasks is a string which is a task name
  
### Example

```
curl -X GET "${baseurl}/app/db/lockview"
{"tasks": ["2021-12-10T21:47:03.230179 update: __all__.review.aspect Lock_Release_End", "2021-12-10T21:47:03.230161 update: __all__.review.aspect Lock_Release_Begin", "2021-12-10T21:47:03.230150 update: __all__.review.aspect Lock_Acquire_End", "2021-12-10T21:47:01.853538 update: __all__.review.aspect Lock_Acquire_Begin", "2021-12-10T21:47:01.853536 update: __all__.review.aspect Lock_Request_End", "2021-12-10T21:47:01.853446 update: __all__.review.aspect Lock_Request_Begin", "2021-12-10T21:46:33.127596 update: __all__.network.analyzer Lock_Release_End", "2021-12-10T21:46:33.127580 update: __all__.network.analyzer Lock_Release_Begin", "2021-12-10T21:46:33.127570 update: __all__.network.analyzer Lock_Acquire_End", "2021-12-10T21:46:32.548059 update: __all__.network.analyzer Lock_Acquire_Begin", "2021-12-10T21:46:32.548056 update: __all__.network.analyzer Lock_Request_End", "2021-12-10T21:46:32.547927 update: __all__.network.analyzer Lock_Request_Begin", "2021-12-10T21:46:32.484747 load: /tmp/tmp659wit5v.network.engine Lock_Release_End", "2021-12-10T21:46:32.484720 load: /tmp/tmp659wit5v.network.engine Lock_Release_Begin", "2021-12-10T21:46:32.484710 load: /tmp/tmp659wit5v.network.engine Lock_Acquire_End", "2021-12-10T21:46:31.555293 load: /tmp/tmp659wit5v.network.engine Lock_Acquire_Begin", "2021-12-10T21:46:31.555285 load: /tmp/tmp659wit5v.network.engine Lock_Request_End", "2021-12-10T21:46:31.555060 load: /tmp/tmp659wit5v.network.engine Lock_Request_Begin"]}
```

## `/app/db/prime` (GET) (JSON)
### Description

Fetch a list of all known state vectors by full name.

### Inputs
_no inputs_

### Outputs
- _unnamed_:list(string)  
  each element of the list is a '.' delimited full name of each state vector of the form `runid.target_name.task_name.algoritm_name.state_vector_name`.
  
### Example

```
curl -X GET "${baseurl}/app/db/prime"
["1.__all__.network.analyzer.test", "2.__all__.review.aspect.test", "2.__all__.review.aspect.__metric__"]
```

## `/app/db/targets` (GET) (JSON)
### Description

Fetch a list of all known targets

### Inputs
_no inputs_

### Outputs
- _unnamed_:list(string)  
  each element of the list is a string representing a target name

### Example

```
curl -X GET "${baseurl}/app/db/targets"
["__all__", "/tmp/tmp659wit5v"]
```

## `/app/db/versions` (GET) (JSON)
### Description

Fetch all versions of all software elements known to the system. Tasks have no version while algorithms, state vectors, and values do. The version list for tasks will always be null while the other are a list of X.Y.Z matching [semantic versioning](https://semver.org/).

### Inputs
_no inputs_

### Outputs
- _unnamed_:[{string:[string]}]  
  each element of the list is a dictionary whose keys are tasks, algorithms, state vectors, and values

### Example

```
curl -X GET "${baseurl}/app/db/versions"
[{"review": null, "network": null}, {"network.analyzer": ["1.0.0"], "review.aspect": ["1.0.0"]}, {"review.aspect.test": ["1.0.0"], "network.analyzer.test": ["1.0.0"]}, {"network.analyzer.test.image": ["1.0.0"], "review.aspect.test.image": ["1.0.0"]}]
```

## `/app/filter/admin` (GET) (JSON)
### Description

Fetch the filter critera that defines what to include and what to exclude for state vectors of DAWGIE adminstrative interest.

### Inputs
_no inputs_

### Outputs
- _unnamed_:{"exclude":{_regex_:[runid]}, "include":{_regex_:[runid]}}
  a JSON object with exclude/include elements that are both dictionaries of the same structure: a set of regular expresions with corresponding runids with an empty list meaning all.

### Example

```
curl -X GET "${baseurl}/app/filter/admin"
{"include": {".__metric__$": []}}
```

## `/app/filter/dev` (GET) (JSON)
### Description

Fetch the filter critera that defines what to include and what to exclude for state vectors of Algorithm Engine (AE) developer interest.

### Inputs
_no inputs_

### Outputs
- _unnamed_:{"exclude":{_regex_:[runid]}, "include":{_regex_:[runid]}}
  a JSON object with exclude/include elements that are both dictionaries of the same structure: a set of regular expresions with corresponding runids with an empty list meaning all.

### Example

```
curl -X GET "${baseurl}/app/filter/dev"
{"exclude": {".__metric__$": []}}
```

## `/app/filter/user` (GET) (JSON)
### Description

Fetch the filter critera that defines what to include and what to exclude for state vectors of Algorithm Engine (AE) end user interest.

### Inputs
_no inputs_

### Outputs
- _unnamed_:{"exclude":{_regex_:[runid]}, "include":{_regex_:[runid]}}
  a JSON object with exclude/include elements that are both dictionaries of the same structure: a set of regular expresions with corresponding runids with an empty list meaning all.

### Example

```
curl -X GET "${baseurl}/app/filter/user"
{"exclude": {".__metric__$": []}}
```

## `/app/pl/log` (GET) (JSON)
### Description

Fetch the last N message sent to the log file. N is configurable via the DAWGIE context file and arguments.

### Inputs
_no inputs_

### Outputs
- _unnamed_:list[{"timeStamp":datestring, "name":pythonmodule, "level":string, "message":string}]  
  each element of the list represents the information in a line of the log file
  
### Example

```
curl -X GET "${baseurl}/app/pl/log"
[{"timeStamp": "2021-12-10 13:47:06,211", "name": "dawgie.db.shelf", "level": "CRITICAL", "message": "called _rotate after open"}, {"timeStamp": "2021-12-10 13:46:35,820", "name": "dawgie.pl.farm", "level": "CRITICAL", "message": "New run ID (2) for algorithm review.aspect trigger by the event: New software changeset baff80d5ecb08ef1370507fb055759973bc462f9"}, {"timeStamp": "2021-12-10 12:50:50,819", "name": "dawgie.pl.farm", "level": "CRITICAL", "message": "New run ID (1) for algorithm network.analyzer trigger by the event: New software changeset baff80d5ecb08ef1370507fb055759973bc462f9"}]
```

## `/app/pl/state` (GET) (JSON)
### Description

The current state of the DAWGIE server (pipline).

### Inputs
_no inputs_

### Outputs
- _unnamed_:{"name":string, "status":string}  
  the name is string representation of the current state and status is always active.

### Example

```
curl -X GET "${baseurl}/app/pl/state"
{"name": "running", "status": "active"}
```

## `/app/run`, (POST)
### Description
### Inputs
### Outputs
### Example

```
curl -X POST "${baseurl}/app/run"
abc
```

## `/app/schedule/crew` (GET)
### Description

Describe the status of the of workers (crew) as to whether they are busy or idle.

### Inputs
_no inputs_

### Outputs
- _unnamed_:{"busy":[string], "idle":integer}  
  each busy list element is the string representation of the task being worked and idle states the number of idle workers waiting for a job
  
### Example

```
curl -X GET "${baseurl}/app/schedule/crew"
{"busy": [], "idle": "1"}
```

## `/app/schedule/doing` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "${baseurl}/app/schedule/doing"
abc
```

## `/app/schedule/events` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "${baseurl}/app/schedule/events"
abc
```

## `/app/schedule/failure` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "${baseurl}/app/schedule/failure"
abc
```

## `/app/schedule/success` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "${baseurl}/app/schedule/success"
abc
```

## `/app/schedule/tasks` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "${baseurl}/app/schedule/tasks"
abc
```

## `/app/schedule/todo` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "${baseurl}/app/schedule/todo"
abc
```

## `/app/search/completion/sv` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "${baseurl}/app/search/completion/sv"
abc
```

## `/app/search/completion/tn` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "${baseurl}/app/search/completion/tn"
abc
```

## `/app/search/ri` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "${baseurl}/app/search/ri"
abc
```

## `/app/search/sv` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "${baseurl}/app/search/sv"
abc
```

## `/app/search/tn` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "${baseurl}/app/search/tn"
abc
```

## `/app/state/status` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "${baseurl}/app/state/status"
abc
```

## `/app/submit` (POST)
### Description
### Inputs
### Outputs
### Example

```
curl -X POST "${baseurl}/app/submit"
abc
```

## `/app/versions` (GET)
### Description
### Inputs
### Outputs
### Example

```
curl -X GET "${baseurl}/app/versions"
abc
```

